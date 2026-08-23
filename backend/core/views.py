import json
import math
from datetime import date
from urllib.parse import urlencode
from urllib.request import urlopen

from django.contrib.auth import authenticate, get_user_model
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Accommodation, Booking, Destination, RoomType, UserProfile
from .serializers import AccommodationSerializer, BookingSerializer, DestinationSerializer, RoomTypeSerializer

User = get_user_model()


def health_check(request):
    return JsonResponse({
        'status': 'ok',
        'service': 'travel-api',
    })


@api_view(['GET'])
def destination_list(request):
    queryset = Destination.objects.all().order_by('-rating')
    serializer = DestinationSerializer(queryset, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def accommodation_list(request):
    accommodations = Accommodation.objects.prefetch_related('room_types').all().order_by('-rating')
    serializer = AccommodationSerializer(accommodations, many=True)
    return Response(serializer.data)


@api_view(['GET', 'POST'])
def admin_destination_list_create(request):
    if request.method == 'GET':
        destinations = Destination.objects.all().order_by('-rating')
        return Response(DestinationSerializer(destinations, many=True).data)

    serializer = DestinationSerializer(data=request.data)
    if serializer.is_valid():
        destination = serializer.save()
        return Response(DestinationSerializer(destination).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH', 'DELETE'])
def admin_destination_detail(request, destination_id):
    try:
        destination = Destination.objects.get(pk=destination_id)
    except Destination.DoesNotExist:
        return Response({'error': 'Không tìm thấy điểm đến.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(DestinationSerializer(destination).data)

    if request.method == 'PATCH':
        serializer = DestinationSerializer(destination, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    destination.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
def admin_accommodation_list_create(request):
    if request.method == 'GET':
        accommodations = Accommodation.objects.prefetch_related('room_types').all().order_by('-rating')
        return Response(AccommodationSerializer(accommodations, many=True).data)

    serializer = AccommodationSerializer(data=request.data)
    if serializer.is_valid():
        accommodation = serializer.save()
        return Response(AccommodationSerializer(accommodation).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH', 'DELETE'])
def admin_accommodation_detail(request, accommodation_id):
    try:
        accommodation = Accommodation.objects.get(pk=accommodation_id)
    except Accommodation.DoesNotExist:
        return Response({'error': 'Không tìm thấy chỗ ở.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(AccommodationSerializer(accommodation).data)

    if request.method == 'PATCH':
        serializer = AccommodationSerializer(accommodation, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    accommodation.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
def admin_room_type_list_create(request, accommodation_id):
    try:
        accommodation = Accommodation.objects.get(pk=accommodation_id)
    except Accommodation.DoesNotExist:
        return Response({'error': 'Không tìm thấy chỗ ở.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(RoomTypeSerializer(accommodation.room_types.all(), many=True).data)

    payload = request.data.copy()
    payload['accommodation'] = accommodation.id
    serializer = RoomTypeSerializer(data=payload)
    if serializer.is_valid():
        room_type = serializer.save(accommodation=accommodation)
        return Response(RoomTypeSerializer(room_type).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH', 'DELETE'])
def admin_room_type_detail(request, room_type_id):
    try:
        room_type = RoomType.objects.get(pk=room_type_id)
    except RoomType.DoesNotExist:
        return Response({'error': 'Không tìm thấy loại phòng.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(RoomTypeSerializer(room_type).data)

    if request.method == 'PATCH':
        serializer = RoomTypeSerializer(room_type, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    room_type.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


def _normalize_tokens(value):
    if not value:
        return []
    return [token.lower() for token in value.replace(',', ' ').replace('-', ' ').split() if token]


def _build_vector(*parts):
    tokens = []
    for part in parts:
        tokens.extend(_normalize_tokens(part))
    vector = {}
    for token in tokens:
        vector[token] = vector.get(token, 0) + 1
    return vector


def _cosine_similarity(a, b):
    all_tokens = set(a) | set(b)
    if not all_tokens:
        return 0.0
    dot = sum(a.get(token, 0) * b.get(token, 0) for token in all_tokens)
    norm_a = math.sqrt(sum(value * value for value in a.values()))
    norm_b = math.sqrt(sum(value * value for value in b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _haversine_km(lat1, lon1, lat2, lon2):
    radius = 6371.0
    lat1_r = math.radians(lat1)
    lat2_r = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(delta_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius * c


def _member_trapezoid(value, left, peak_start, peak_end, right):
    if value <= left or value >= right:
        return 0.0
    if left < value < peak_start:
        return (value - left) / (peak_start - left)
    if peak_start <= value <= peak_end:
        return 1.0
    if peak_end < value < right:
        return (right - value) / (right - peak_end)
    return 0.0


def _weather_score_for_day(destination_latitude, travel_date):
    month = (travel_date.month if isinstance(travel_date, date) else date.today().month)
    simulated_temp = 24 + math.sin((month - 1) / 12 * 2 * math.pi) * 8 + (destination_latitude / 30)
    simulated_rain = 35 + abs(math.sin(month / 12 * 2 * math.pi)) * 45
    simulated_wind = 18 + abs(math.cos(month / 12 * 2 * math.pi)) * 22

    temp_mem = _member_trapezoid(simulated_temp, 15, 24, 30, 40)
    rain_mem = 1.0 - _member_trapezoid(simulated_rain, 0, 20, 50, 100)
    wind_mem = 1.0 - _member_trapezoid(simulated_wind, 0, 10, 30, 60)
    return 0.5 * temp_mem + 0.3 * rain_mem + 0.2 * wind_mem


def _budget_score(cost_estimate, budget_estimate):
    if budget_estimate <= 0:
        return 0.0
    if cost_estimate <= budget_estimate:
        return 1.0
    return max(0.0, 1 - ((cost_estimate - budget_estimate) / budget_estimate))


@api_view(['GET'])
def recommendation_view(request):
    preferences = request.GET.get('user_preferences', '')
    budget_estimate = float(request.GET.get('budget_estimate', 0) or 0)
    latitude = float(request.GET.get('latitude', 0) or 0)
    longitude = float(request.GET.get('longitude', 0) or 0)
    travel_date = request.GET.get('travel_date')
    top_n = int(request.GET.get('top_n', 5) or 5)

    try:
        travel_date = date.fromisoformat(travel_date) if travel_date else date.today()
    except ValueError:
        travel_date = date.today()

    preference_vectors = _build_vector(preferences, preferences.replace(',', ' '))
    all_destinations = Destination.objects.all().order_by('-rating')

    destination_results = []
    for destination in all_destinations:
        destination_text = ' '.join([
            destination.name,
            destination.description,
            destination.category,
        ])
        destination_vector = _build_vector(destination_text)
        preference_score = _cosine_similarity(preference_vectors, destination_vector)
        weather_score = _weather_score_for_day(destination.latitude, travel_date)

        room_prices = list(RoomType.objects.filter(
            accommodation__latitude__isnull=False,
            accommodation__longitude__isnull=False,
        ).values_list('base_price', flat=True)[:10])
        if room_prices:
            estimated_cost = sum(room_prices) / len(room_prices)
        else:
            category_factor = {'biển': 1800000, 'núi': 1500000, 'thành phố': 2000000, 'ẩm thực': 1300000}.get(destination.category, 1500000)
            estimated_cost = category_factor

        budget_score = _budget_score(estimated_cost, budget_estimate or estimated_cost)
        distance = _haversine_km(latitude, longitude, destination.latitude, destination.longitude)
        distance_score = 1 / (1 + distance / 80)

        final_score = (0.4 * preference_score) + (0.25 * weather_score) + (0.2 * budget_score) + (0.15 * distance_score)

        destination_results.append({
            'id': destination.id,
            'name': destination.name,
            'description': destination.description,
            'category': destination.category,
            'rating': destination.rating,
            'latitude': destination.latitude,
            'longitude': destination.longitude,
            'distance_km': round(distance, 1),
            'estimated_cost': int(estimated_cost),
            'preference_score': round(preference_score, 4),
            'weather_score': round(weather_score, 4),
            'budget_score': round(budget_score, 4),
            'distance_score': round(distance_score, 4),
            'score': round(final_score, 4),
        })

    destination_results = sorted(destination_results, key=lambda item: item['score'], reverse=True)
    return Response({'results': destination_results[:max(1, top_n)]})


@api_view(['POST'])
def booking_create(request):
    serializer = BookingSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    room_type = serializer.validated_data['room_type']
    check_in = serializer.validated_data['check_in']
    check_out = serializer.validated_data['check_out']

    if check_in < date.today() or check_out <= check_in:
        return Response({'non_field_errors': ['Ngày nhận phải từ hôm nay và ngày trả phải sau ngày nhận.']}, status=status.HTTP_400_BAD_REQUEST)

    overlapping = Booking.objects.filter(
        room_type=room_type,
        status__in=['pending', 'confirmed'],
        check_in__lt=check_out,
        check_out__gt=check_in,
    )

    if overlapping.count() >= room_type.stock:
        return Response({'non_field_errors': ['Không còn phòng trống cho khoảng thời gian này.']}, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        locked_room = RoomType.objects.select_for_update().get(pk=room_type.pk)
        overlapping_locked = Booking.objects.filter(
            room_type=locked_room,
            status__in=['pending', 'confirmed'],
            check_in__lt=check_out,
            check_out__gt=check_in,
        ).select_for_update()
        if overlapping_locked.count() >= locked_room.stock:
            return Response({'non_field_errors': ['Không còn phòng trống cho khoảng thời gian này.']}, status=status.HTTP_400_BAD_REQUEST)
        booking = serializer.save()

    return Response(BookingSerializer(booking).data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def payment_init(request):
    booking_id = request.data.get('booking_id')
    amount = request.data.get('amount', 0)
    return_url = request.data.get('return_url') or 'http://localhost:5173/payment-return'

    try:
        booking = Booking.objects.get(pk=booking_id)
    except Booking.DoesNotExist:
        return Response({'error': 'Không tìm thấy đặt phòng.'}, status=status.HTTP_404_NOT_FOUND)

    try:
        amount_value = int(amount)
    except (TypeError, ValueError):
        return Response({'error': 'Số tiền thanh toán không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)

    if amount_value <= 0:
        return Response({'error': 'Số tiền thanh toán phải lớn hơn 0.'}, status=status.HTTP_400_BAD_REQUEST)

    params = urlencode({
        'booking_id': booking.id,
        'status': 'success',
        'amount': amount_value,
        'ref': f'BOOK-{booking.id}',
    })
    redirect_url = f'{return_url}?{params}'

    return Response({
        'booking_id': booking.id,
        'amount': amount_value,
        'status': 'pending',
        'redirect_url': redirect_url,
        'message': 'Đã khởi tạo thanh toán sandbox thành công.',
    })


@api_view(['GET'])
def payment_return(request):
    booking_id = request.GET.get('booking_id')
    status_value = request.GET.get('status', 'failed')

    try:
        booking = Booking.objects.get(pk=booking_id)
    except Booking.DoesNotExist:
        return Response({'success': False, 'error': 'Không tìm thấy đặt phòng.'}, status=status.HTTP_404_NOT_FOUND)

    if status_value == 'success':
        booking.status = 'confirmed'
        booking.save(update_fields=['status'])
        return Response({
            'success': True,
            'booking_id': booking.id,
            'status': booking.status,
            'message': 'Thanh toán thành công. Đặt phòng đã được xác nhận.',
        })

    booking.status = 'cancelled'
    booking.save(update_fields=['status'])
    return Response({
        'success': False,
        'booking_id': booking.id,
        'status': booking.status,
        'message': 'Thanh toán thất bại hoặc bị hủy.',
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def weather_forecast(request):
    try:
        latitude = float(request.GET.get('latitude', 0) or 0)
        longitude = float(request.GET.get('longitude', 0) or 0)
        target_date = request.GET.get('date') or str(date.today())
        target_date = date.fromisoformat(target_date)
    except ValueError:
        return Response({'error': 'latitude, longitude và date không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)

    params = {
        'latitude': latitude,
        'longitude': longitude,
        'daily': 'temperature_2m_max,precipitation_probability_max,wind_speed_10m_max',
        'timezone': 'auto',
        'forecast_days': 16,
    }

    url = 'https://api.open-meteo.com/v1/forecast?' + urlencode(params)
    try:
        with urlopen(url, timeout=15) as response:
            payload = json.loads(response.read().decode('utf-8'))
    except Exception as exc:
        return Response({'error': f'Không thể lấy dữ liệu thời tiết: {exc}'}, status=status.HTTP_502_BAD_GATEWAY)

    daily = payload.get('daily', {})
    dates = daily.get('time', [])
    temps = daily.get('temperature_2m_max', [])
    rain = daily.get('precipitation_probability_max', [])
    winds = daily.get('wind_speed_10m_max', [])

    if not dates:
        return Response({'error': 'Không có dữ liệu thời tiết.'}, status=status.HTTP_404_NOT_FOUND)

    index = 0
    for i, value in enumerate(dates):
        if value == str(target_date):
            index = i
            break
    if index >= len(temps):
        index = min(index, len(temps) - 1)

    temperature = float(temps[index]) if index < len(temps) and temps[index] is not None else 0.0
    precipitation = float(rain[index]) if index < len(rain) and rain[index] is not None else 0.0
    wind_speed = float(winds[index]) if index < len(winds) and winds[index] is not None else 0.0

    temp_membership = max(0.0, min(1.0, (temperature - 15) / (24 - 15) if 15 < temperature < 24 else 1.0 if 24 <= temperature <= 30 else (40 - temperature) / (40 - 30) if 30 < temperature < 40 else 0.0))
    rain_membership = max(0.0, min(1.0, 1 - (precipitation / 100)))
    wind_membership = max(0.0, min(1.0, 1 - (wind_speed / 60)))
    weather_score = 0.5 * temp_membership + 0.3 * rain_membership + 0.2 * wind_membership

    return Response({
        'date': str(target_date),
        'temperature': round(temperature, 1),
        'precipitation_probability': round(precipitation, 1),
        'wind_speed': round(wind_speed, 1),
        'weather_score': round(weather_score, 4),
        'temperature_membership': round(temp_membership, 4),
        'rain_membership': round(rain_membership, 4),
        'wind_membership': round(wind_membership, 4),
    })


@api_view(['POST'])
def register_user(request):
    username = request.data.get('username', '').strip()
    email = request.data.get('email', '').strip()
    password = request.data.get('password', '')

    if not username or not email or not password:
        return Response({'error': 'username, email và password là bắt buộc.'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        return Response({'error': 'Tên đăng nhập đã tồn tại.'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(username=username, email=email, password=password)
    UserProfile.objects.get_or_create(user=user)

    return Response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def login_user(request):
    username = request.data.get('username', '').strip()
    password = request.data.get('password', '')

    user = authenticate(username=username, password=password)
    if user is None:
        return Response({'error': 'Tên đăng nhập hoặc mật khẩu không đúng.'}, status=status.HTTP_401_UNAUTHORIZED)

    profile = UserProfile.objects.filter(user=user).first()
    return Response({
        'success': True,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
        },
        'profile': {
            'travel_preferences': profile.travel_preferences if profile else [],
            'budget_estimate': str(profile.budget_estimate) if profile else '0',
            'free_text': profile.free_text if profile else '',
        },
    })


@api_view(['GET'])
def profile_detail(request, user_id):
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return Response({'error': 'Không tìm thấy người dùng.'}, status=status.HTTP_404_NOT_FOUND)

    profile, _ = UserProfile.objects.get_or_create(user=user)
    return Response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'travel_preferences': profile.travel_preferences,
        'budget_estimate': str(profile.budget_estimate),
        'free_text': profile.free_text,
    })
