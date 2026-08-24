import json
import math
import os
from datetime import date
from urllib.parse import urlencode
from urllib.request import urlopen

import requests
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.core.cache import cache
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from sentence_transformers.util import cos_sim

from django.core.mail import send_mail

from .models import Accommodation, AccommodationReview, Booking, ChatMessage, Destination, RoomType, SearchHistory, UserProfile
from .embedding import encode_text
from .serializers import (
    AccommodationReviewSerializer,
    AccommodationSerializer,
    BookingSerializer,
    ChatMessageSerializer,
    DestinationSerializer,
    RoomTypeSerializer,
    SearchHistorySerializer,
    UserProfileSerializer,
)

User = get_user_model()


def api_not_found(request, exception=None):
    return JsonResponse({
        'detail': 'API endpoint not found.',
        'path': request.path,
    }, status=404)


def api_server_error(request):
    return JsonResponse({
        'detail': 'Internal server error.',
    }, status=500)


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


@api_view(['GET'])
def destination_lookup(request):
    query = (request.GET.get('q') or '').strip()
    if not query:
        return Response({'results': []}, status=status.HTTP_400_BAD_REQUEST)

    cache_key = f'destination_lookup:{query.lower()}'
    cached = cache.get(cache_key)
    if cached is not None:
        return Response(cached)

    try:
        nominatim_response = requests.get(
            'https://nominatim.openstreetmap.org/search',
            params={'q': query, 'format': 'jsonv2', 'limit': 5, 'addressdetails': 1},
            headers={'User-Agent': 'DuLichThongMinhDemo/1.0'},
            timeout=15,
        )
        nominatim_response.raise_for_status()
        places = nominatim_response.json()
    except Exception:
        places = []

    results = []
    for place in places:
        lat = float(place.get('lat', 0) or 0)
        lon = float(place.get('lon', 0) or 0)
        place_name = place.get('display_name') or place.get('name') or query
        image_url = ''
        unsplash_key = os.getenv('UNSPLASH_ACCESS_KEY')
        if unsplash_key:
            try:
                image_response = requests.get(
                    'https://api.unsplash.com/search/photos',
                    params={'query': query, 'per_page': 1, 'orientation': 'landscape'},
                    headers={'Authorization': f'Client-ID {unsplash_key}'},
                    timeout=15,
                )
                if image_response.status_code == 200:
                    image_payload = image_response.json()
                    items = image_payload.get('results', [])
                    if items:
                        image_url = items[0].get('urls', {}).get('regular') or items[0].get('urls', {}).get('small') or ''
            except Exception:
                image_url = ''
        else:
            image_url = 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80'

        results.append({
            'name': place.get('name') or query,
            'full_name': place_name,
            'latitude': lat,
            'longitude': lon,
            'category': 'biển' if 'biển' in query.lower() else 'thành phố' if 'tp' in query.lower() or 'thành phố' in query.lower() else 'núi' if 'núi' in query.lower() else 'ẩm thực',
            'image_url': image_url,
            'source': 'nominatim',
        })

    if not results:
        results = [{
            'name': query,
            'full_name': query,
            'latitude': 0.0,
            'longitude': 0.0,
            'category': 'biển',
            'image_url': 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80',
            'source': 'fallback',
        }]

    cache.set(cache_key, results, timeout=3600)
    return Response({'results': results})


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


def get_weather_score(latitude, longitude, target_date):
    cache_key = f'weather:{latitude}:{longitude}:{target_date}'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    params = {
        'latitude': latitude,
        'longitude': longitude,
        'daily': 'temperature_2m_max,precipitation_probability_max,wind_speed_10m_max',
        'timezone': 'auto',
        'forecast_days': 16,
    }
    url = 'https://api.open-meteo.com/v1/forecast?' + urlencode(params)
    with urlopen(url, timeout=15) as response:
        payload = json.loads(response.read().decode('utf-8'))

    daily = payload.get('daily', {})
    dates = daily.get('time', [])
    temps = daily.get('temperature_2m_max', [])
    rain = daily.get('precipitation_probability_max', [])
    winds = daily.get('wind_speed_10m_max', [])
    if not dates:
        raise ValueError('Không có dữ liệu thời tiết.')

    index = dates.index(str(target_date)) if str(target_date) in dates else 0
    temperature = float(temps[index]) if index < len(temps) and temps[index] is not None else 0.0
    precipitation = float(rain[index]) if index < len(rain) and rain[index] is not None else 0.0
    wind_speed = float(winds[index]) if index < len(winds) and winds[index] is not None else 0.0
    temp_membership = _member_trapezoid(temperature, 15, 24, 30, 40)
    rain_membership = max(0.0, min(1.0, 1 - (precipitation / 100)))
    wind_membership = max(0.0, min(1.0, 1 - (wind_speed / 60)))
    body = {
        'date': str(target_date),
        'temperature': round(temperature, 1),
        'precipitation_probability': round(precipitation, 1),
        'wind_speed': round(wind_speed, 1),
        'weather_score': round(0.5 * temp_membership + 0.3 * rain_membership + 0.2 * wind_membership, 4),
        'temperature_membership': round(temp_membership, 4),
        'rain_membership': round(rain_membership, 4),
        'wind_membership': round(wind_membership, 4),
    }
    cache.set(cache_key, body, timeout=3600)
    return body


def _budget_score(cost_estimate, budget_estimate):
    if budget_estimate <= 0:
        return 0.0
    if cost_estimate <= budget_estimate:
        return 1.0
    return max(0.0, 1 - ((cost_estimate - budget_estimate) / budget_estimate))


def _recommendation_results(preferences, budget_estimate, latitude, longitude, travel_date, top_n):
    preference_vector = encode_text(preferences)
    all_destinations = Destination.objects.all().order_by('-rating')

    destination_results = []
    for destination in all_destinations:
        destination_text = ' '.join([
            destination.name,
            destination.description,
            destination.category,
        ])
        if destination.embedding_cache is None:
            destination.embedding_cache = encode_text(destination_text)
            Destination.objects.filter(pk=destination.pk).update(embedding_cache=destination.embedding_cache)
        preference_score = float(cos_sim(preference_vector, destination.embedding_cache).item())
        weather_data = get_weather_score(destination.latitude, destination.longitude, travel_date)
        weather_score = weather_data['weather_score']

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

    return sorted(destination_results, key=lambda item: item['score'], reverse=True)[:max(1, top_n)]


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

    try:
        results = _recommendation_results(preferences, budget_estimate, latitude, longitude, travel_date, top_n)
    except Exception as exc:
        return Response({'error': f'Không thể tạo gợi ý: {exc}'}, status=status.HTTP_502_BAD_GATEWAY)
    return Response({'results': results})


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

    tnm_code = os.getenv('VNPAY_TMN_CODE')
    hash_secret = os.getenv('VNPAY_HASH_SECRET')
    if tnm_code and hash_secret:
        params = {
            'vnp_TmnCode': tnm_code,
            'vnp_Amount': str(amount_value * 100),
            'vnp_Command': 'pay',
            'vnp_CreateDate': date.today().strftime('%Y%m%d%H%M%S'),
            'vnp_CurrCode': 'VND',
            'vnp_IpAddr': '127.0.0.1',
            'vnp_Locale': 'vn',
            'vnp_OrderInfo': f'Booking_{booking.id}',
            'vnp_OrderType': 'other',
            'vnp_ReturnUrl': return_url,
            'vnp_TxnRef': f'BOOK-{booking.id}',
        }
        query = urlencode(params)
        redirect_url = f'https://sandbox.vnpayment.vn/paymentv2/vpcpay.html?{query}'
        gateway_name = 'vnpay'
    else:
        params = urlencode({
            'booking_id': booking.id,
            'status': 'success',
            'amount': amount_value,
            'ref': f'BOOK-{booking.id}',
        })
        redirect_url = f'{return_url}?{params}'
        gateway_name = 'sandbox'

    return Response({
        'booking_id': booking.id,
        'amount': amount_value,
        'status': 'pending',
        'provider': gateway_name,
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
        if booking.user.email:
            try:
                send_mail(
                    'Xác nhận đặt phòng thành công',
                    f'Xin chào {booking.user.username}, đặt phòng của bạn đã được xác nhận cho {booking.room_type.name} từ {booking.check_in} đến {booking.check_out}.',
                    settings.EMAIL_HOST_USER if hasattr(settings, 'EMAIL_HOST_USER') else 'noreply@example.com',
                    [booking.user.email],
                    fail_silently=True,
                )
            except Exception:
                pass
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


@api_view(['POST'])
def booking_cancel(request, booking_id):
    try:
        booking = Booking.objects.select_related('user', 'room_type').get(pk=booking_id)
    except Booking.DoesNotExist:
        return Response({'error': 'Không tìm thấy đặt phòng.'}, status=status.HTTP_404_NOT_FOUND)

    refund_amount = int(request.data.get('refund_amount', 0) or 0)
    if booking.status == 'cancelled':
        return Response({
            'booking_id': booking.id,
            'status': booking.status,
            'refund_amount': int(booking.refund_amount),
            'message': 'Đặt phòng này đã bị hủy trước đó.',
        })

    booking.cancel_booking(refund_amount=refund_amount)
    return Response({
        'booking_id': booking.id,
        'status': booking.status,
        'refund_amount': int(booking.refund_amount),
        'message': 'Đặt phòng đã được hủy và hoàn tiền theo yêu cầu.',
    })


@api_view(['GET'])
def route_planning(request):
    try:
        start_lat = float(request.GET.get('start_lat', 0) or 0)
        start_lng = float(request.GET.get('start_lng', 0) or 0)
        end_lat = float(request.GET.get('end_lat', 0) or 0)
        end_lng = float(request.GET.get('end_lng', 0) or 0)
    except ValueError:
        return Response({'error': 'start_lat, start_lng, end_lat, end_lng không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)

    ors_api_key = os.getenv('ORS_API_KEY')
    if ors_api_key:
        try:
            response = requests.post(
                'https://api.openrouteservice.org/v2/directions/driving-car/json',
                headers={'Authorization': ors_api_key, 'Content-Type': 'application/json'},
                json={'coordinates': [[start_lng, start_lat], [end_lng, end_lat]], 'format': 'json'},
                timeout=20,
            )
            if response.status_code == 200:
                payload = response.json()
                route = payload.get('routes', [{}])[0]
                summary = route.get('summary', {})
                distance_km = round((summary.get('distance', 0) or 0) / 1000, 1)
                duration_minutes = max(10, int((summary.get('duration', 0) or 0) / 60))
                google_maps_url = (
                    'https://www.google.com/maps/dir/?api=1'
                    f'&origin={start_lat},{start_lng}'
                    f'&destination={end_lat},{end_lng}'
                    '&travelmode=driving'
                )
                return Response({
                    'distance_km': distance_km,
                    'duration_minutes': duration_minutes,
                    'google_maps_url': google_maps_url,
                    'distance_label': f'{distance_km} km',
                    'duration_label': f'{duration_minutes} phút',
                    'provider': 'openrouteservice',
                })
        except Exception:
            pass

    distance_km = _haversine_km(start_lat, start_lng, end_lat, end_lng)
    speed_kmh = 35.0
    duration_minutes = max(10, int((distance_km / speed_kmh) * 60))
    google_maps_url = (
        'https://www.google.com/maps/dir/?api=1'
        f'&origin={start_lat},{start_lng}'
        f'&destination={end_lat},{end_lng}'
        '&travelmode=driving'
    )

    return Response({
        'distance_km': round(distance_km, 1),
        'duration_minutes': duration_minutes,
        'google_maps_url': google_maps_url,
        'distance_label': f'{round(distance_km, 1)} km',
        'duration_label': f'{duration_minutes} phút',
        'provider': 'haversine-fallback',
    })


@api_view(['GET'])
def recommendation_explanation(request):
    query_params = request.GET
    preferences = query_params.get('user_preferences', '')
    budget_estimate = float(query_params.get('budget_estimate', 0) or 0)
    latitude = float(query_params.get('latitude', 0) or 0)
    longitude = float(query_params.get('longitude', 0) or 0)
    travel_date = query_params.get('travel_date')
    top_n = int(query_params.get('top_n', 5) or 5)

    try:
        travel_date = date.fromisoformat(travel_date) if travel_date else date.today()
    except ValueError:
        travel_date = date.today()

    try:
        results = _recommendation_results(preferences, budget_estimate, latitude, longitude, travel_date, top_n)
    except Exception as exc:
        return Response({'error': f'Không thể tạo gợi ý: {exc}'}, status=status.HTTP_502_BAD_GATEWAY)
    if not results:
        return Response({'explanation': 'Không có điểm đến phù hợp cho tiêu chí hiện tại.', 'top_destination': None})

    top_destination = results[0]
    destination_name = top_destination.get('name', 'điểm đến được đề xuất')
    budget_value = f'{int(budget_estimate):,} đ' if budget_estimate else 'ngân sách linh hoạt'
    date_value = travel_date.strftime('%d/%m/%Y')
    prompt = (
        f'Người dùng ưu tiên: {preferences or "du lịch đa dạng"}. '
        f'Ngân sách ước tính: {budget_value}. '
        f'Ngày dự kiến đến: {date_value}. '
        f'Điểm đến hàng đầu: {destination_name}. '
        'Viết một đoạn giải thích ngắn gọn, thân thiện và cá nhân hóa bằng tiếng Việt, '
        'không dài quá 2 câu, nhấn mạnh lý do phù hợp với sở thích và ngân sách.'
    )

    gemini_api_key = os.getenv('GEMINI_API_KEY')
    if gemini_api_key:
        try:
            import requests
            payload = {
                'contents': [{
                    'parts': [{'text': prompt}],
                }],
                'generationConfig': {'temperature': 0.4, 'maxOutputTokens': 180},
            }
            response = requests.post(
                'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent',
                params={'key': gemini_api_key},
                json=payload,
                timeout=20,
            )
            if response.status_code == 200:
                candidates = response.json().get('candidates', [])
                if candidates:
                    text = candidates[0].get('content', {}).get('parts', [{}])[0].get('text', '')
                    if text:
                        return Response({
                            'explanation': text.strip(),
                            'top_destination': top_destination,
                        })
        except Exception:
            pass

    fallback = (
        f'Bạn đang phù hợp với {destination_name} vì điểm đến này đồng bộ với sở thích của bạn, '
        f'đảm bảo trải nghiệm du lịch tốt trong ngân sách khoảng {budget_value} và phù hợp với thời điểm {date_value}.'
    )
    return Response({
        'explanation': fallback,
        'top_destination': top_destination,
    })


@api_view(['GET'])
def weather_forecast(request):
    try:
        latitude = float(request.GET.get('latitude', 0) or 0)
        longitude = float(request.GET.get('longitude', 0) or 0)
        target_date = request.GET.get('date') or str(date.today())
        target_date = date.fromisoformat(target_date)
    except ValueError:
        return Response({'error': 'latitude, longitude và date không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        return Response(get_weather_score(latitude, longitude, target_date))
    except Exception as exc:
        return Response({'error': f'Không thể lấy dữ liệu thời tiết: {exc}'}, status=status.HTTP_502_BAD_GATEWAY)


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


@api_view(['GET', 'PATCH'])
def profile_detail(request, user_id):
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return Response({'error': 'Không tìm thấy người dùng.'}, status=status.HTTP_404_NOT_FOUND)

    profile, _ = UserProfile.objects.get_or_create(user=user)

    if request.method == 'PATCH':
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            profile.refresh_from_db()
            return Response({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'travel_preferences': profile.travel_preferences,
                'budget_estimate': str(profile.budget_estimate),
                'free_text': profile.free_text,
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'travel_preferences': profile.travel_preferences,
        'budget_estimate': str(profile.budget_estimate),
        'free_text': profile.free_text,
    })


@api_view(['GET', 'POST'])
def search_history_view(request):
    user_id = request.GET.get('user_id') or request.data.get('user_id')

    if request.method == 'GET':
        queryset = SearchHistory.objects.select_related('user').all().order_by('-created_at')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        return Response(SearchHistorySerializer(queryset, many=True).data)

    payload = request.data.copy()
    if 'user' not in payload and 'user_id' in payload:
        payload['user'] = payload['user_id']

    serializer = SearchHistorySerializer(data=payload)
    if serializer.is_valid():
        history = serializer.save()
        return Response(SearchHistorySerializer(history).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
def chat_message_list(request):
    user_id = request.GET.get('user_id') or request.data.get('user_id')
    receiver_id = request.GET.get('receiver_id') or request.data.get('receiver_id')

    if request.method == 'GET':
        queryset = ChatMessage.objects.select_related('sender', 'receiver').all().order_by('created_at')
        if user_id and receiver_id:
            queryset = queryset.filter(
                (Q(sender_id=user_id) & Q(receiver_id=receiver_id)) |
                (Q(sender_id=receiver_id) & Q(receiver_id=user_id))
            )
        return Response(ChatMessageSerializer(queryset, many=True).data)

    serializer = ChatMessageSerializer(data=request.data)
    if serializer.is_valid():
        message = serializer.save()
        return Response(ChatMessageSerializer(message).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
def review_list_create(request):
    if request.method == 'GET':
        accommodation_id = request.GET.get('accommodation')
        queryset = AccommodationReview.objects.select_related('user', 'accommodation').all().order_by('-created_at')
        if accommodation_id:
            queryset = queryset.filter(accommodation_id=accommodation_id)
        return Response(AccommodationReviewSerializer(queryset, many=True).data)

    serializer = AccommodationReviewSerializer(data=request.data)
    if serializer.is_valid():
        review = serializer.save()
        return Response(AccommodationReviewSerializer(review).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
