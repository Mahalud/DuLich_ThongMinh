import base64
import hashlib
import hmac
import json
import logging
import math
import os
import re
import unicodedata
import time
import uuid
from pathlib import PurePosixPath
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from urllib.parse import urlencode

import requests
import redis
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login, logout, update_session_auth_hash
from django.contrib.auth.tokens import default_token_generator
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.db import transaction
from django.db.models import Avg, Count, Q
from django.db.models.functions import TruncDate
from django.contrib.gis.db.models.functions import Distance
from django.http import HttpResponseRedirect, JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from django.utils.encoding import force_str
from django.utils import timezone
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Amenity, Accommodation, AccommodationReview, Booking, ChatMessage, Destination, RecommendationFeedback, RecommendationLog, RoomType, SearchHistory, SitePage, SitePageSection, Tour, TourBooking, TourDeparture, TourStop, TravelPost, TravelPostLike, UserProfile
from .cancellations import cancellation_refund_preview
from .auth_security import password_errors, record_attempt, throttle_key, throttle_remaining
from .embedding import encode_text
from .weather_utils import WEATHER_PREFERENCES, calculate_weather_score, unavailable_weather_body, weather_cache_key, weather_score_body
from .recommendation_weights import DEFAULT_WEIGHTS, get_user_weights, recalculate_user_weights, record_booked_feedback, weights_as_dict
from .serializers import (
    AccommodationReviewSerializer,
    AccommodationSerializer,
    AdminBookingSerializer,
    AmenitySerializer,
    BookingSerializer,
    ChatMessageSerializer,
    DestinationSerializer,
    RoomTypeSerializer,
    SearchHistorySerializer,
    SitePageSectionSerializer,
    SitePageSerializer,
    TourBookingSerializer,
    TourDepartureSerializer,
    TourDetailSerializer,
    TourSerializer,
    TourStopSerializer,
    TravelPostSerializer,
    UserProfileSerializer,
)

User = get_user_model()
logger = logging.getLogger(__name__)


@api_view(['GET'])
def public_statistics(request):
    """Small public counters used by the About page."""
    return Response({
        'destination_count': Destination.objects.count(),
        'tour_count': Tour.objects.filter(is_active=True).count(),
        'accommodation_count': Accommodation.objects.count(),
        'travel_post_count': TravelPost.objects.count(),
        'average_rating': round(float(AccommodationReview.objects.aggregate(value=Avg('rating'))['value'] or 0), 1),
    })


def require_admin(request):
    if not request.user.is_authenticated:
        return Response({'detail': 'Vui lòng đăng nhập để tiếp tục.'}, status=status.HTTP_401_UNAUTHORIZED)
    if not (request.user.is_staff or request.user.is_superuser):
        return Response({'detail': 'Bạn cần quyền quản trị viên để thực hiện thao tác này.'}, status=status.HTTP_403_FORBIDDEN)
    return None


@api_view(['GET'])
def public_site_page(request, slug):
    page = get_object_or_404(SitePage.objects.prefetch_related('sections'), slug=slug)
    return Response(SitePageSerializer(page).data)


@api_view(['PUT'])
def admin_site_page(request, slug):
    denied = require_admin(request)
    if denied:
        return denied
    page = get_object_or_404(SitePage, slug=slug)
    serializer = SitePageSerializer(page, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    page = serializer.save(updated_by=request.user)
    return Response(SitePageSerializer(page).data)


@api_view(['POST'])
def admin_site_page_sections(request, slug):
    denied = require_admin(request)
    if denied:
        return denied
    page = get_object_or_404(SitePage, slug=slug)
    payload = request.data.copy()
    if payload.get('order') in (None, ''):
        payload['order'] = page.sections.count()
    serializer = SitePageSectionSerializer(data=payload)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    section = serializer.save(page=page)
    return Response(SitePageSectionSerializer(section).data, status=status.HTTP_201_CREATED)


@api_view(['PUT', 'DELETE'])
def admin_site_page_section_detail(request, slug, section_id):
    denied = require_admin(request)
    if denied:
        return denied
    page = get_object_or_404(SitePage, slug=slug)
    section = get_object_or_404(SitePageSection, page=page, pk=section_id)
    if request.method == 'DELETE':
        section.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    serializer = SitePageSectionSerializer(section, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    return Response(SitePageSectionSerializer(serializer.save()).data)


@api_view(['POST'])
def admin_site_page_sections_reorder(request, slug):
    denied = require_admin(request)
    if denied:
        return denied
    page = get_object_or_404(SitePage, slug=slug)
    section_ids = request.data.get('section_ids')
    sections = list(page.sections.all())
    if (not isinstance(section_ids, list)
            or any(not isinstance(section_id, int) or isinstance(section_id, bool) for section_id in section_ids)
            or len(section_ids) != len(sections)
            or set(section_ids) != {section.pk for section in sections}):
        return Response({'detail': 'Danh sách thứ tự phải chứa đủ mỗi phần đúng một lần.'}, status=status.HTTP_400_BAD_REQUEST)
    section_by_id = {section.pk: section for section in sections}
    reordered = [section_by_id[section_id] for section_id in section_ids]
    for order, section in enumerate(reordered):
        section.order = order
    with transaction.atomic():
        SitePageSection.objects.bulk_update(reordered, ['order'])
    page.refresh_from_db()
    return Response(SitePageSerializer(page).data)


@api_view(['GET'])
def admin_integrations_status(request):
    denied = require_admin(request)
    if denied:
        return denied

    return Response({
        'gemini': bool(os.getenv('GEMINI_API_KEY')),
        'openrouteservice': bool(os.getenv('ORS_API_KEY')),
        'vnpay': all(os.getenv(key) for key in ('VNPAY_TMN_CODE', 'VNPAY_HASH_SECRET')),
        'momo': all(os.getenv(key) for key in ('MOMO_PARTNER_CODE', 'MOMO_ACCESS_KEY', 'MOMO_SECRET_KEY')),
        'unsplash': bool(os.getenv('UNSPLASH_ACCESS_KEY')),
    })


@api_view(['GET'])
def admin_statistics(request):
    denied = require_admin(request)
    if denied:
        return denied

    days_param = request.GET.get('days', '7')
    try:
        days = int(days_param)
        if days <= 0:
            days = 7
    except (TypeError, ValueError):
        days = 7

    start_date = timezone.now() - timedelta(days=days)

    # 1. Total searches & searches by day
    # Keep demonstration accounts out of operational statistics; guests and
    # real users without a profile remain included.
    real_or_guest_user = Q(user__isnull=True) | Q(user__profile__is_demo=False) | Q(user__profile__isnull=True)
    logs_qs = RecommendationLog.objects.filter(created_at__gte=start_date).filter(real_or_guest_user)
    has_search_ids = logs_qs.filter(search_id__isnull=False).exists()
    if has_search_ids:
        total_searches = logs_qs.values('search_id').distinct().count()
    else:
        total_searches = logs_qs.values('created_at', 'user_id').distinct().count()

    # searches_by_day: mang {date, count}
    day_counts = defaultdict(int)
    if has_search_ids:
        day_rows = (
            logs_qs.annotate(day=TruncDate('created_at'))
            .values('day')
            .annotate(count=Count('search_id', distinct=True))
        )
    else:
        day_rows = (
            logs_qs.annotate(day=TruncDate('created_at'))
            .values('day')
            .annotate(count=Count('id'))
        )
    for row in day_rows:
        if row['day']:
            day_counts[row['day'].isoformat()] = row['count']

    start_day = (timezone.now() - timedelta(days=days - 1)).date()
    end_day = timezone.now().date()
    current_day = start_day
    searches_by_day = []
    while current_day <= end_day:
        d_str = current_day.isoformat()
        searches_by_day.append({
            'date': d_str,
            'count': day_counts.get(d_str, 0),
        })
        current_day += timedelta(days=1)

    # 2. Top destinations in RecommendationLog
    top_dest_rows = (
        logs_qs.values('destination_id', 'destination__name')
        .annotate(
            count=Count('id'),
            avg_score=Avg('score'),
        )
        .order_by('-count', '-avg_score')[:10]
    )
    top_destinations = [
        {
            'destination_id': row['destination_id'],
            'name': row['destination__name'],
            'count': row['count'],
            'appearance_count': row['count'],
            'avg_score': round(float(row['avg_score']), 2) if row['avg_score'] is not None else 0.0,
        }
        for row in top_dest_rows
    ]

    # 3. Top booked destinations (Booking + TourBooking with status='confirmed')
    booked_counts_map = defaultdict(lambda: {'booking_count': 0, 'tour_booking_count': 0, 'total': 0})

    # Accommodation bookings
    acc_bookings = (
        Booking.objects.filter(
            status='confirmed',
            created_at__gte=start_date,
            room_type__accommodation__destination__isnull=False,
        ).filter(Q(user__profile__is_demo=False) | Q(user__profile__isnull=True))
        .values('room_type__accommodation__destination')
        .annotate(c=Count('id'))
    )
    for row in acc_bookings:
        did = row['room_type__accommodation__destination']
        booked_counts_map[did]['booking_count'] += row['c']
        booked_counts_map[did]['total'] += row['c']

    # Tour bookings
    confirmed_tour_bookings = TourBooking.objects.filter(
        status='confirmed',
        created_at__gte=start_date,
    ).filter(Q(user__profile__is_demo=False) | Q(user__profile__isnull=True)).select_related('departure')

    tour_ids = {
        tb.tour_id or (tb.departure.tour_id if tb.departure_id else None)
        for tb in confirmed_tour_bookings
    }
    tour_ids.discard(None)

    tour_to_dests = defaultdict(set)
    if tour_ids:
        for stop in TourStop.objects.filter(tour_id__in=tour_ids).values('tour_id', 'destination_id'):
            tour_to_dests[stop['tour_id']].add(stop['destination_id'])

    for tb in confirmed_tour_bookings:
        tid = tb.tour_id or (tb.departure.tour_id if tb.departure_id else None)
        if tid and tid in tour_to_dests:
            for did in tour_to_dests[tid]:
                booked_counts_map[did]['tour_booking_count'] += 1
                booked_counts_map[did]['total'] += 1

    dest_ids = list(booked_counts_map.keys())
    name_map = {}
    if dest_ids:
        name_map = {
            d['id']: d['name']
            for d in Destination.objects.filter(id__in=dest_ids).values('id', 'name')
        }

    top_booked_destinations = [
        {
            'destination_id': did,
            'name': name_map.get(did, f'Điểm đến #{did}'),
            'booking_count': data['booking_count'],
            'tour_booking_count': data['tour_booking_count'],
            'total_bookings': data['total'],
            'count': data['total'],
        }
        for did, data in sorted(booked_counts_map.items(), key=lambda x: x[1]['total'], reverse=True)[:10]
    ]

    return Response({
        'total_searches': total_searches,
        'searches_by_day': searches_by_day,
        'top_destinations': top_destinations,
        'top_booked_destinations': top_booked_destinations,
        'days': days,
    })


def api_not_found(request, exception=None):
    return JsonResponse({
        'detail': 'Không tìm thấy đường dẫn API.',
        'path': request.path,
    }, status=404)


def api_server_error(request):
    return JsonResponse({
        'detail': 'Máy chủ đang gặp sự cố. Vui lòng thử lại sau.',
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
def amenity_list(request):
    return Response(AmenitySerializer(Amenity.objects.all(), many=True).data)


@api_view(['POST'])
def admin_amenity_list_create(request):
    denied = require_admin(request)
    if denied:
        return denied
    serializer = AmenitySerializer(data=request.data)
    if serializer.is_valid():
        amenity = serializer.save()
        return Response(AmenitySerializer(amenity).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT', 'PATCH', 'DELETE'])
def admin_amenity_detail(request, amenity_id):
    denied = require_admin(request)
    if denied:
        return denied
    amenity = get_object_or_404(Amenity, pk=amenity_id)
    if request.method == 'DELETE':
        with transaction.atomic():
            for room_type in RoomType.objects.all().only('id', 'amenities').iterator():
                keys = room_type.amenities or []
                if amenity.key in keys:
                    room_type.amenities = [key for key in keys if key != amenity.key]
                    room_type.save(update_fields=['amenities'])
            amenity.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = AmenitySerializer(amenity, data=request.data, partial=request.method == 'PATCH')
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def accommodation_list(request):
    accommodations = Accommodation.objects.prefetch_related('room_types').all().order_by('-rating')
    serializer = AccommodationSerializer(accommodations, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def accommodations_near_destination(request, destination_id):
    destination = get_object_or_404(Destination, id=destination_id)
    if destination.vi_tri is None:
        return Response({'error': 'Điểm đến chưa có dữ liệu vị trí.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        radius_km = float(request.GET.get('radius', 10))
    except (TypeError, ValueError):
        return Response({'error': 'Bán kính phải là một số hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)
    if radius_km <= 0 or radius_km > 200:
        return Response({'error': 'Bán kính phải lớn hơn 0 và không quá 200 km.'}, status=status.HTTP_400_BAD_REQUEST)

    accommodations = Accommodation.objects.filter(vi_tri__isnull=False).annotate(
        distance_m=Distance('vi_tri', destination.vi_tri, spheroid=False)
    ).filter(distance_m__lte=radius_km * 1000).order_by('distance_m').prefetch_related('room_types')
    return Response({
        'destination_id': destination.id,
        'radius_km': radius_km,
        'results': AccommodationSerializer(accommodations, many=True).data,
    })


@api_view(['GET'])
def destination_lookup(request):
    query = (request.GET.get('q') or '').strip()
    if not query:
        return Response({'results': []}, status=status.HTTP_400_BAD_REQUEST)

    include_image = request.GET.get('include_image', 'true').strip().lower() not in {'0', 'false', 'no'}
    photo_query = (request.GET.get('image_query') or query).strip()
    cache_key = f'destination_lookup:v2:{query.lower()}:photo={photo_query.lower()}:image={int(include_image)}'
    cached = cache.get(cache_key)
    if cached is not None:
        return Response(cached if isinstance(cached, dict) and 'results' in cached else {'results': cached})

    try:
        nominatim_response = requests.get(
            'https://nominatim.openstreetmap.org/search',
            params={'q': query, 'format': 'jsonv2', 'limit': 5, 'addressdetails': 1, 'countrycodes': 'vn', 'accept-language': 'vi'},
            headers={'User-Agent': 'DuLichThongMinhDemo/1.0', 'Accept-Language': 'vi'},
            timeout=10,
        )
        nominatim_response.raise_for_status()
        places = nominatim_response.json()
    except requests.Timeout:
        logger.warning('destination_lookup fallback: Nominatim request timed out; using local results.')
        places = []
    except requests.RequestException as exc:
        logger.warning('destination_lookup fallback: Nominatim API request failed: %s; using local results.', exc)
        places = []
    except ValueError as exc:
        logger.warning('destination_lookup fallback: Nominatim returned invalid JSON: %s; using local results.', exc)
        places = []

    image_url = ''
    if include_image:
        unsplash_key = os.getenv('UNSPLASH_ACCESS_KEY')
        if not unsplash_key:
            logger.warning('destination_lookup fallback: UNSPLASH_ACCESS_KEY is missing; using default image.')
        else:
            try:
                image_response = requests.get(
                    'https://api.unsplash.com/search/photos',
                    params={'query': photo_query, 'per_page': 1, 'orientation': 'landscape'},
                    headers={'Authorization': f'Client-ID {unsplash_key}'},
                    timeout=10,
                )
                if image_response.status_code == 200:
                    image_payload = image_response.json()
                    items = image_payload.get('results', [])
                    if items:
                        image_url = items[0].get('urls', {}).get('regular') or items[0].get('urls', {}).get('small') or ''
                else:
                    logger.warning('destination_lookup fallback: Unsplash API returned status %s; using default image.', image_response.status_code)
            except requests.Timeout:
                logger.warning('destination_lookup fallback: Unsplash request timed out; using default image.')
            except requests.RequestException as exc:
                logger.warning('destination_lookup fallback: Unsplash API request failed: %s; using default image.', exc)
            except ValueError as exc:
                logger.warning('destination_lookup fallback: Unsplash returned invalid JSON: %s; using default image.', exc)
        if not image_url:
            image_url = 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80'

    results = []
    for place in places:
        results.append({
            'name': place.get('name') or query,
            'full_name': place.get('display_name') or place.get('name') or query,
            'latitude': float(place.get('lat', 0) or 0),
            'longitude': float(place.get('lon', 0) or 0),
            'category': '\u0062i\u1ec3n' if '\u0062i\u1ec3n' in query.lower() else '\u0074h\u00e0nh ph\u1ed1' if 'tp' in query.lower() or '\u0074h\u00e0nh ph\u1ed1' in query.lower() else '\u006e\u00fai' if '\u006e\u00fai' in query.lower() else '\u1ea9m th\u1ef1c',
            'image_url': image_url,
            'source': 'nominatim',
        })

    if not results:
        results = [{
            'name': query,
            'full_name': query,
            'latitude': 0.0,
            'longitude': 0.0,
            'category': '\u0062i\u1ec3n',
            'image_url': image_url,
            'source': 'fallback',
        }]

    response_data = {'results': results}
    cache.set(cache_key, response_data, timeout=3600)
    return Response(response_data)


@api_view(['GET'])
def destination_reverse_lookup(request):
    """Resolve browser coordinates to a Vietnamese place label."""
    try:
        latitude = float(request.GET.get('latitude'))
        longitude = float(request.GET.get('longitude'))
    except (TypeError, ValueError):
        return Response({'error': 'Tọa độ không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        return Response({'error': 'Tọa độ nằm ngoài phạm vi hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)
    cache_key = f'destination_reverse_lookup:v1:{latitude:.4f}:{longitude:.4f}'
    cached = cache.get(cache_key)
    if cached:
        return Response(cached)
    try:
        response = requests.get(
            'https://nominatim.openstreetmap.org/reverse',
            params={'lat': latitude, 'lon': longitude, 'format': 'jsonv2', 'addressdetails': 1, 'accept-language': 'vi'},
            headers={'User-Agent': 'DuLichThongMinhDemo/1.0', 'Accept-Language': 'vi'},
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        logger.warning('destination_reverse_lookup failed: %s', exc)
        return Response({'error': 'Chưa xác định được tên nơi này. Bạn có thể tìm thành phố hoặc khu vực bên dưới.'}, status=status.HTTP_502_BAD_GATEWAY)
    address = payload.get('address') or {}
    # Nominatim reverse has no countrycodes filter; enforce the Vietnam scope on its result.
    if address.get('country_code', '').lower() != 'vn':
        return Response({'error': 'Vị trí hiện tại chưa được xác định là ở Việt Nam. Hãy tìm thành phố hoặc khu vực bên dưới.'}, status=status.HTTP_400_BAD_REQUEST)
    place_name = next((address.get(key) for key in ('city', 'town', 'municipality', 'village', 'county', 'state') if address.get(key)), 'Việt Nam')
    result = {'name': place_name, 'latitude': latitude, 'longitude': longitude}
    cache.set(cache_key, result, 60 * 60 * 24)
    return Response(result)

@api_view(['GET', 'POST'])
def admin_destination_list_create(request):
    denied = require_admin(request)
    if denied:
        return denied
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
    denied = require_admin(request)
    if denied:
        return denied
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
    denied = require_admin(request)
    if denied:
        return denied
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
    denied = require_admin(request)
    if denied:
        return denied
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
    denied = require_admin(request)
    if denied:
        return denied
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
    denied = require_admin(request)
    if denied:
        return denied
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


@api_view(['GET'])
def public_room_type_detail(request, room_type_id):
    """Public room details needed to restore a booking page after reload."""
    room_type = get_object_or_404(
        RoomType.objects.select_related('accommodation'),
        pk=room_type_id,
    )
    return Response(RoomTypeSerializer(room_type).data)


@api_view(['GET'])
def admin_booking_list(request):
    denied = require_admin(request)
    if denied:
        return denied
    bookings = Booking.objects.select_related('user', 'room_type').all()
    return Response(AdminBookingSerializer(bookings, many=True, context={'request': request}).data)


@api_view(['PATCH'])
def admin_booking_status(request, booking_id):
    denied = require_admin(request)
    if denied:
        return denied
    booking = get_object_or_404(Booking, pk=booking_id)
    next_status = request.data.get('status')
    if next_status not in {'confirmed', 'cancelled'}:
        return Response({'error': 'Trạng thái chỉ có thể là đã xác nhận hoặc đã hủy.'}, status=status.HTTP_400_BAD_REQUEST)
    if next_status == 'cancelled':
        booking, ok, error = _cancel_booking(
            booking,
            is_admin=True,
            requested_refund=request.data.get('refund_amount', 0),
        )
        if not ok:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
        return Response(AdminBookingSerializer(booking, context={'request': request}).data)
    booking.status = 'confirmed'
    booking.save(update_fields=['status'])
    _record_confirmed_booking_feedback(booking, is_tour=False)
    return Response(AdminBookingSerializer(booking, context={'request': request}).data)


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


def get_weather_score(latitude, longitude, target_date, weather_preference='balanced'):
    cache_key = weather_cache_key(latitude, longitude, target_date)
    cache_started_at = time.perf_counter()
    logger.info('BẮT ĐẦU truy vấn cache thời tiết: %s (backend=%s)', cache_key, settings.CACHES['default']['BACKEND'])
    cached = cache.get(cache_key)
    logger.info('XONG truy vấn cache thời tiết sau %.3f giây (%s)', time.perf_counter() - cache_started_at, 'HIT' if cached is not None else 'MISS')
    if cached is not None:
        return calculate_weather_score(cached, weather_preference)

    params = {
        'latitude': latitude,
        'longitude': longitude,
        'daily': 'temperature_2m_max,precipitation_probability_max,wind_speed_10m_max',
        'timezone': 'auto',
        'forecast_days': settings.WEATHER_MAX_FORECAST_DAYS,
    }
    weather_started_at = time.perf_counter()
    logger.info('BẮT ĐẦU gọi Open-Meteo: %s', cache_key)
    try:
        response = requests.get(
            'https://api.open-meteo.com/v1/forecast',
            params=params,
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
        logger.info('XONG gọi Open-Meteo sau %.3f giây: %s', time.perf_counter() - weather_started_at, cache_key)

        daily = payload.get('daily', {})
        dates = daily.get('time', [])
        temps = daily.get('temperature_2m_max', [])
        rain = daily.get('precipitation_probability_max', [])
        winds = daily.get('wind_speed_10m_max', [])

        if str(target_date) not in dates:
            raw_weather = unavailable_weather_body(target_date)
            cache.set(cache_key, raw_weather, timeout=3 * 60 * 60)
            return calculate_weather_score(raw_weather, weather_preference)
        index = dates.index(str(target_date))
        if (index >= len(temps) or index >= len(rain) or index >= len(winds)
                or temps[index] is None or rain[index] is None or winds[index] is None):
            raw_weather = unavailable_weather_body(target_date)
            cache.set(cache_key, raw_weather, timeout=3 * 60 * 60)
            return calculate_weather_score(raw_weather, weather_preference)
        temperature = float(temps[index])
        precipitation = float(rain[index])
        wind_speed = float(winds[index])
    except Exception as exc:
        logger.warning('Lỗi khi gọi Open-Meteo (%s): %s; dùng điểm thời tiết trung tính.', cache_key, exc)
        raw_weather = unavailable_weather_body(target_date)
        cache.set(cache_key, raw_weather, timeout=3 * 60 * 60)
        return calculate_weather_score(raw_weather, weather_preference)
    raw_weather = weather_score_body(target_date, temperature, precipitation, wind_speed)
    cache_write_started_at = time.perf_counter()
    logger.info('BẮT ĐẦU ghi cache thời tiết: %s', cache_key)
    cache.set(cache_key, raw_weather, timeout=3 * 60 * 60)
    logger.info('XONG ghi cache thời tiết sau %.3f giây', time.perf_counter() - cache_write_started_at)
    return calculate_weather_score(raw_weather, weather_preference)


def _budget_score(cost_estimate, budget_estimate):
    if budget_estimate <= 0:
        return 0.0
    if cost_estimate <= budget_estimate:
        return 1.0
    return max(0.0, 1 - ((cost_estimate - budget_estimate) / budget_estimate))


def _cosine_similarity(left, right):
    """Calculate cosine similarity without importing the ML runtime at startup."""
    if not left or not right:
        return 0.0
    dot_product = sum(a * b for a, b in zip(left, right))
    left_magnitude = math.sqrt(sum(a * a for a in left))
    right_magnitude = math.sqrt(sum(b * b for b in right))
    if not left_magnitude or not right_magnitude:
        return 0.0
    return dot_product / (left_magnitude * right_magnitude)


def _clean_preference_input(value):
    """Trim user preference text, remove control characters, and cap embedding input size."""
    value = ''.join(
        char for char in str(value or '')
        if unicodedata.category(char) not in {'Cc', 'Cs'}
    )
    value = ' '.join(value.split())[:200]
    return value.strip(' ,;')


def _weights_for_available_criteria(weights, has_preference, has_budget, has_origin):
    """Redistribute personalized criterion weights only across criteria present in this search."""
    active = {
        'w1': has_preference,
        'w2': True,  # Weather is always scored for the selected travel date.
        'w3': has_budget,
        'w4': has_origin,
    }
    values = {key: max(0.0, float((weights or DEFAULT_WEIGHTS).get(key, 0))) if enabled else 0.0
              for key, enabled in active.items()}
    total = sum(values.values())
    if total <= 0:
        values = {key: (1.0 if key == 'w2' else 0.0) for key in active}
        return values
    return {key: value / total for key, value in values.items()}


def _recommendation_results(preferences, budget_estimate, latitude, longitude, travel_date, top_n, weights=None, weather_preference='balanced'):
    from .embedding import destination_embedding_text, expand_preferences

    preferences = _clean_preference_input(preferences)
    preference_query = expand_preferences(preferences)
    has_preference = bool(preference_query)
    has_budget = float(budget_estimate or 0) > 0
    has_origin = latitude is not None and longitude is not None
    weights = _weights_for_available_criteria(weights, has_preference, has_budget, has_origin)
    embedding_started_at = time.perf_counter()
    preference_vector = None
    if has_preference:
        logger.info('BẮT ĐẦU encode embedding preferences')
        preference_vector = encode_text(preference_query)
        logger.info('XONG encode embedding sau %.3f giây', time.perf_counter() - embedding_started_at)

    destination_query_started_at = time.perf_counter()
    logger.info('BẮT ĐẦU query database Destination')
    all_destinations = list(Destination.objects.all().order_by('-rating'))
    logger.info('XONG query database Destination sau %.3f giây (%d bản ghi)', time.perf_counter() - destination_query_started_at, len(all_destinations))

    weather_batch_started_at = time.perf_counter()
    logger.info('BẮT ĐẦU gọi Open-Meteo song song cho %d điểm đến', len(all_destinations))
    with ThreadPoolExecutor(max_workers=min(8, max(1, len(all_destinations)))) as executor:
        weather_results = list(executor.map(
            lambda destination: get_weather_score(destination.latitude, destination.longitude, travel_date, weather_preference),
            all_destinations,
        ))
    logger.info('XONG gọi Open-Meteo song song sau %.3f giây', time.perf_counter() - weather_batch_started_at)

    destination_results = []
    for destination, weather_data in zip(all_destinations, weather_results):
        destination_text = destination_embedding_text(destination)
        if destination.embedding_cache is None:
            destination.embedding_cache = encode_text(destination_text)
            Destination.objects.filter(pk=destination.pk).update(embedding_cache=destination.embedding_cache)
        preference_raw = _cosine_similarity(preference_vector, destination.embedding_cache) if has_preference else None
        weather_score = weather_data['weather_score']

        category_factor = {'biển': 1800000, 'núi': 1500000, 'thành phố': 2000000, 'ẩm thực': 1300000}.get(destination.category, 1500000)
        estimated_cost = destination.reference_cost or category_factor

        budget_score = _budget_score(estimated_cost, budget_estimate) if has_budget else None
        distance_started_at = time.perf_counter()
        logger.info('BẮT ĐẦU tính distance: %s', destination.name)
        distance = _haversine_km(latitude, longitude, destination.latitude, destination.longitude) if has_origin else None
        logger.info('XONG tính distance sau %.3f giây: %s', time.perf_counter() - distance_started_at, destination.name)
        distance_max_km = max(0.0, float(settings.DISTANCE_MAX_KM))
        distance_score = None if distance is None else (1.0 if distance_max_km == 0 and distance == 0 else (
            0.0 if distance_max_km == 0 else 1 - min(distance / distance_max_km, 1)
        ))

        destination_results.append({
            'id': destination.id,
            'name': destination.name,
            'description': destination.description,
            'category': destination.category,
            'image_url': destination.image_url,
            'rating': destination.rating,
            'latitude': destination.latitude,
            'longitude': destination.longitude,
            'distance_km': round(distance, 1) if distance is not None else None,
            'estimated_cost': int(estimated_cost),
            'preference_score': preference_raw,
            'preference_raw': preference_raw,
            'preference_matched': None,
            'weather_score': round(weather_score, 4),
            'weather_available': weather_data.get('weather_available', bool(weather_data.get('weather'))),
            'weather': weather_data.get('weather', {
                'temperature_c': None, 'rain_probability': None, 'wind_kmh': None,
                'summary': 'Chưa có dữ liệu thời tiết',
            }),
            'budget_score': round(budget_score, 4) if budget_score is not None else None,
            'budget_overage': max(0, int(estimated_cost - budget_estimate)) if has_budget else None,
            'distance_score': round(distance_score, 4) if distance_score is not None else None,
            'score': 0.0,
        })

    # Stretch preference scores only when the query has at least one clear semantic match.
    if destination_results:
        raw_values = [item['preference_raw'] for item in destination_results if item['preference_raw'] is not None]
        raw_min, raw_max = (min(raw_values), max(raw_values)) if raw_values else (0.0, 0.0)
        preference_matched = has_preference and raw_max > settings.PREFERENCE_MATCH_MIN
        for item in destination_results:
            if has_preference:
                if preference_matched:
                    raw_score = item['preference_raw']
                    preference_score = (raw_score - raw_min) / (raw_max - raw_min) if raw_max > raw_min else 0.5
                else:
                    preference_score = item['preference_raw']
                item['preference_score'] = round(preference_score, 4)
                item['preference_matched'] = preference_matched
            else:
                preference_score = 0.0

            budget_component = item['budget_score'] or 0.0
            item['score'] = round(
                weights['w1'] * preference_score
                + weights['w2'] * item['weather_score']
                + weights['w3'] * budget_component
                + (weights['w4'] * item['distance_score'] if item['distance_score'] is not None else 0),
                4,
            )
            if item['preference_raw'] is not None:
                item['preference_raw'] = round(item['preference_raw'], 6)
    return sorted(destination_results, key=lambda item: item['score'], reverse=True)[:max(1, top_n)]


@api_view(['GET'])
def recommendation_view(request):
    request_started_at = time.perf_counter()
    logger.info('BẮT ĐẦU recommendation request')
    redis_started_at = time.perf_counter()
    try:
        redis_client = redis.Redis.from_url(
            settings.REDIS_URL,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        redis_client.ping()
        logger.info('XONG Redis PING sau %.3f giây: OK', time.perf_counter() - redis_started_at)
    except redis.RedisError as exc:
        logger.warning('XONG Redis PING sau %.3f giây: lỗi %s', time.perf_counter() - redis_started_at, exc)
    preferences = _clean_preference_input(request.GET.get('user_preferences', ''))
    weather_preference = request.GET.get('weather_preference', 'balanced')
    if weather_preference not in WEATHER_PREFERENCES:
        return Response({'error': 'Lựa chọn thời tiết không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        budget_estimate = float(request.GET.get('budget_estimate', 0) or 0)
        latitude_raw = request.GET.get('latitude')
        longitude_raw = request.GET.get('longitude')
        if bool(latitude_raw) != bool(longitude_raw):
            return Response({'error': 'Cần cung cấp cả vĩ độ và kinh độ cho vị trí xuất phát.'}, status=status.HTTP_400_BAD_REQUEST)
        latitude = float(latitude_raw) if latitude_raw else None
        longitude = float(longitude_raw) if longitude_raw else None
        top_n = int(request.GET.get('top_n', 5) or 5)
    except (TypeError, ValueError):
        return Response({'error': 'Ngân sách, tọa độ và số lượng gợi ý phải là số hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)
    if latitude is not None and (not -90 <= latitude <= 90 or not -180 <= longitude <= 180):
        return Response({'error': 'Vĩ độ phải trong khoảng từ -90 đến 90, kinh độ phải trong khoảng từ -180 đến 180.'}, status=status.HTTP_400_BAD_REQUEST)
    travel_date = request.GET.get('travel_date')
    try:
        travel_date = date.fromisoformat(travel_date) if travel_date else date.today()
    except ValueError:
        return Response({'error': 'Ngày đi không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)
    if travel_date < date.today():
        return Response({'error': 'Ngày đi không được ở quá khứ.'}, status=status.HTTP_400_BAD_REQUEST)
    if travel_date > date.today() + timedelta(days=settings.WEATHER_MAX_FORECAST_DAYS - 1):
        return Response({'error': f'Ngày đi phải nằm trong cửa sổ dự báo thời tiết tối đa {settings.WEATHER_MAX_FORECAST_DAYS} ngày, tính cả hôm nay.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        personalized_weights = get_user_weights(request.user)
        criteria_used = ['weather']
        if preferences:
            criteria_used.insert(0, 'preference')
        if budget_estimate > 0:
            criteria_used.append('budget')
        if latitude is not None:
            criteria_used.append('distance')
        weights_used = _weights_for_available_criteria(
            personalized_weights,
            has_preference=bool(preferences),
            has_budget=budget_estimate > 0,
            has_origin=latitude is not None,
        )
        results = _recommendation_results(
            preferences, budget_estimate, latitude, longitude, travel_date, top_n, weights_used, weather_preference,
        )
        logger.info('XONG recommendation request sau %.3f giây', time.perf_counter() - request_started_at)
    except Exception as exc:
        return Response({'error': f'Không thể tạo gợi ý: {exc}'}, status=status.HTTP_502_BAD_GATEWAY)
    if results:
        user = request.user if request.user.is_authenticated else None
        search_id = uuid.uuid4()
        logs_to_create = [
            RecommendationLog(
                user=user,
                destination_id=item['id'],
                score=float(item.get('score', 0)),
                search_id=search_id,
            )
            for item in results
        ]
        RecommendationLog.objects.bulk_create(logs_to_create)
        if user:
            SearchHistory.objects.create(
                user=user,
                query=preferences,
                preferences=[item.strip() for item in preferences.split(',') if item.strip()],
                budget_estimate=max(0, int(budget_estimate)),
                latitude=latitude if latitude is not None else 0,
                longitude=longitude if longitude is not None else 0,
                travel_date=travel_date,
                top_n=top_n,
                weather_preference=weather_preference,
                destination_id=results[0]['id'],
            )
            profile, _ = UserProfile.objects.get_or_create(user=user)
            if profile.weather_preference != weather_preference:
                profile.weather_preference = weather_preference
                profile.save(update_fields=['weather_preference', 'updated_at'])

    notes = []
    if not preferences:
        notes.append('Chưa nhập sở thích nên chưa tính tiêu chí này.')
    if budget_estimate <= 0:
        notes.append('Chưa nhập ngân sách nên chưa tính tiêu chí này.')
    if latitude is None:
        notes.append('Chưa chọn vị trí xuất phát nên chưa tính khoảng cách.')
    if preferences and results and results[0].get('preference_matched') is False:
        notes.append(
            f"Chưa có điểm đến nào khớp rõ với '{preferences}'; kết quả đang xếp chủ yếu theo các tiêu chí còn lại."
        )

    return Response({
        'results': results,
        'weights_used': weights_used,
        'criteria_used': criteria_used,
        'notes': notes,
    })


@api_view(['POST'])
def parse_recommendation_query(request):
    """Start an asynchronous natural-language parse and return its offline fallback."""
    from .natural_language import normalize_trip_query, parse_trip_query_rules, vietnam_today

    data = request.data
    query = normalize_trip_query(data.get('query', '') if hasattr(data, 'get') else '')
    if not query:
        return Response({'error': 'Vui lòng nhập câu mô tả chuyến đi.'}, status=status.HTTP_400_BAD_REQUEST)

    identity_kind = 'user' if request.user.is_authenticated else 'ip'
    identity = request.user.pk if request.user.is_authenticated else (request.META.get('REMOTE_ADDR') or 'unknown')
    throttle = throttle_key('parse-trip-query', identity_kind, identity)
    retry_after = throttle_remaining([throttle], 20)
    if retry_after:
        return Response(
            {'error': f'Bạn đã dùng hết 20 lượt phân tích trong một giờ. Hãy thử lại sau {retry_after} giây.', 'retry_after_seconds': retry_after},
            status=status.HTTP_429_TOO_MANY_REQUESTS,
            headers={'Retry-After': str(retry_after)},
        )
    record_attempt([throttle], 60 * 60)

    fallback = parse_trip_query_rules(query, today=vietnam_today())
    from .tasks import parse_trip_query_task
    task = parse_trip_query_task.delay(query, fallback)
    return Response({'task_id': task.id, 'fallback': fallback}, status=status.HTTP_202_ACCEPTED)


@api_view(['POST'])
def assistant_ask(request):
    """Answer a public travel question from the local knowledge index."""
    from .rag import NO_INFORMATION_ANSWER, extractive_answer, retrieve_knowledge

    data = request.data if hasattr(request.data, 'get') else {}
    question = normalize_trip_text(data.get('question', ''))
    previous_question = normalize_trip_text(data.get('previous_question', ''))[:300]
    if not question:
        return Response({'error': 'Vui lòng nhập câu hỏi.'}, status=status.HTTP_400_BAD_REQUEST)

    identity_kind = 'user' if request.user.is_authenticated else 'ip'
    identity = request.user.pk if request.user.is_authenticated else (request.META.get('REMOTE_ADDR') or 'unknown')
    throttle = throttle_key('rag-assistant', identity_kind, identity)
    retry_after = throttle_remaining([throttle], 20)
    if retry_after:
        return Response(
            {'error': f'Bạn đã dùng hết 20 lượt hỏi trong một giờ. Hãy thử lại sau {retry_after} giây.',
             'retry_after_seconds': retry_after},
            status=status.HTTP_429_TOO_MANY_REQUESTS,
            headers={'Retry-After': str(retry_after)},
        )
    record_attempt([throttle], 60 * 60)

    retrieval_question = question
    if len(question.split()) < 6 and previous_question:
        retrieval_question = f'{question} {previous_question}'[:600]
    chunks = retrieve_knowledge(retrieval_question)
    if not chunks:
        fallback = {'answer': NO_INFORMATION_ANSWER, 'citations': [], 'source': 'extractive'}
        return Response({'task_id': None, 'fallback': fallback}, status=status.HTTP_202_ACCEPTED)

    fallback = extractive_answer(chunks)
    from .tasks import generate_rag_answer_task
    task = generate_rag_answer_task.delay(retrieval_question, chunks, fallback)
    return Response({'task_id': task.id, 'fallback': fallback}, status=status.HTTP_202_ACCEPTED)


def normalize_trip_text(value):
    """Normalize an assistant question, dropping controls and capping its size."""
    text = ''.join(char for char in str(value or '') if unicodedata.category(char) not in {'Cc', 'Cs'})
    return ' '.join(text.split())[:300].strip()


@api_view(['POST'])
def recommendation_feedback(request):
    """Lưu hành động với một kết quả gợi ý và chạy lại trọng số khi đủ dữ liệu."""
    if not request.user.is_authenticated:
        return Response({'detail': 'Vui lòng đăng nhập để gửi phản hồi gợi ý.'}, status=status.HTTP_401_UNAUTHORIZED)

    destination_id = request.data.get('destination_id')
    action = request.data.get('action')
    valid_actions = {choice[0] for choice in RecommendationFeedback.ACTION_CHOICES}
    if action not in valid_actions:
        return Response({'error': 'Hành động phản hồi không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)
    destination = get_object_or_404(Destination, pk=destination_id)

    scores = {}
    for field_name in ('preference_score', 'weather_score', 'budget_score', 'distance_score'):
        try:
            score = float(request.data.get(field_name))
        except (TypeError, ValueError):
            return Response({'error': f'{field_name} phải là số hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)
        if not 0 <= score <= 1:
            return Response({'error': f'{field_name} phải nằm trong khoảng từ 0 đến 1.'}, status=status.HTTP_400_BAD_REQUEST)
        scores[field_name] = score

    feedback = RecommendationFeedback.objects.create(
        user=request.user,
        destination=destination,
        action=action,
        **scores,
    )
    weight_record = recalculate_user_weights(request.user)
    return Response({
        'id': feedback.id,
        'action': feedback.action,
        'destination_id': destination.id,
        'weights_used': get_user_weights(request.user),
        'weights_stored': weights_as_dict(weight_record),
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def tour_list(request):
    category = request.GET.get('category')
    tours = Tour.objects.filter(is_active=True)
    if category:
        tours = tours.filter(category=category)
    tours = tours.order_by('-created_at')
    return Response(TourSerializer(tours, many=True).data)


@api_view(['GET'])
def tour_detail(request, tour_id):
    tour = get_object_or_404(
        Tour.objects.prefetch_related('stops__destination', 'departures__bookings'),
        pk=tour_id,
        is_active=True,
    )
    return Response(TourDetailSerializer(tour).data)


@api_view(['POST'])
def tour_booking_create(request, tour_id):
    tour = get_object_or_404(Tour, pk=tour_id, is_active=True)
    if not request.user.is_authenticated:
        return Response({'detail': 'Vui lòng đăng nhập để đặt tour.'}, status=status.HTTP_401_UNAUTHORIZED)
    departure = tour.departures.filter(departure_date__gte=timezone.localdate(), is_cancelled=False).first()
    if not departure:
        return Response({'error': 'Tour này chưa có lịch khởi hành phù hợp.'}, status=status.HTTP_400_BAD_REQUEST)
    return tour_departure_booking(request, departure.id)


@api_view(['POST'])
def tour_departure_booking(request, departure_id):
    if not request.user.is_authenticated:
        return Response({'detail': 'Vui lòng đăng nhập để đặt tour.'}, status=status.HTTP_401_UNAUTHORIZED)

    with transaction.atomic():
        try:
            departure = TourDeparture.objects.select_for_update().select_related('tour').get(pk=departure_id, is_cancelled=False)
        except TourDeparture.DoesNotExist:
            return Response({'error': 'Không tìm thấy chuyến khởi hành hoặc chuyến đã bị hủy.'}, status=status.HTTP_404_NOT_FOUND)

        if departure.departure_date < timezone.localdate():
            return Response({'error': 'Chuyến đi này đã qua ngày khởi hành.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            adults = int(request.data.get('num_adults', 1))
            children = int(request.data.get('num_children', 0))
        except (ValueError, TypeError):
            return Response({'error': 'Số lượng người tham gia không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)

        if adults < 1:
            return Response({'error': 'Cần ít nhất 1 người lớn tham gia tour.'}, status=status.HTTP_400_BAD_REQUEST)
        if children < 0:
            return Response({'error': 'Số lượng trẻ em không thể âm.'}, status=status.HTTP_400_BAD_REQUEST)

        guest_phone = str(request.data.get('guest_phone', '')).strip()
        if not guest_phone:
            return Response({'error': 'Vui lòng cung cấp số điện thoại liên hệ.'}, status=status.HTTP_400_BAD_REQUEST)

        requested = adults + children
        used = sum(
            (b.num_adults + b.num_children)
            for b in departure.bookings.select_for_update().filter(status__in=['pending', 'confirmed'])
        )
        if used + requested > departure.slots_total:
            return Response({'error': 'Số chỗ còn lại không đủ.'}, status=status.HTTP_400_BAD_REQUEST)

        tour = departure.tour
        price_adult = tour.price_adult or 0
        price_child = tour.price_child or 0
        is_single_room = bool(request.data.get('is_single_room', False))
        supplement = tour.single_room_supplement if is_single_room else 0
        total_price = (adults * price_adult) + (children * price_child) + supplement

        booking = TourBooking.objects.create(
            user=request.user,
            tour=tour,
            departure=departure,
            departure_date=departure.departure_date,
            num_guests=requested,
            num_adults=adults,
            num_children=children,
            is_single_room=is_single_room,
            guest_phone=guest_phone,
            total_price=total_price,
            status='pending',
        )
    return Response(TourBookingSerializer(booking, context={'request': request}).data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'POST'])
def admin_tours(request):
    denied = require_admin(request)
    if denied: return denied
    if request.method == 'GET':
        tours = Tour.objects.prefetch_related('stops__destination', 'departures').order_by('-created_at')
        return Response(TourDetailSerializer(tours, many=True).data)
    serializer = TourSerializer(data=request.data)
    if serializer.is_valid():
        tour = serializer.save()
        return Response(TourDetailSerializer(tour).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
def admin_tour_detail(request, tour_id):
    denied = require_admin(request)
    if denied: return denied
    tour = get_object_or_404(Tour.objects.prefetch_related('stops__destination', 'departures'), pk=tour_id)
    if request.method == 'GET': return Response(TourDetailSerializer(tour).data)
    if request.method == 'DELETE': tour.delete(); return Response(status=status.HTTP_204_NO_CONTENT)
    serializer = TourSerializer(tour, data=request.data, partial=True)
    if serializer.is_valid():
        updated = serializer.save()
        return Response(TourDetailSerializer(updated).data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def admin_tour_stops(request, tour_id):
    denied = require_admin(request)
    if denied: return denied
    tour = get_object_or_404(Tour, pk=tour_id)
    serializer = TourStopSerializer(data=request.data)
    if serializer.is_valid():
        saved = serializer.save(tour=tour)
        return Response(TourStopSerializer(saved).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT', 'PATCH', 'DELETE'])
def admin_tour_stop_detail(request, tour_id, stop_id):
    denied = require_admin(request)
    if denied:
        return denied
    tour = get_object_or_404(Tour, pk=tour_id)
    stop = get_object_or_404(TourStop, pk=stop_id, tour=tour)
    if request.method == 'DELETE':
        stop.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    serializer = TourStopSerializer(stop, data=request.data, partial=request.method == 'PATCH')
    if serializer.is_valid():
        return Response(TourStopSerializer(serializer.save(tour=tour)).data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
def admin_tour_departures(request, tour_id):
    denied = require_admin(request)
    if denied: return denied
    tour = get_object_or_404(Tour, pk=tour_id)
    if request.method == 'GET':
        deps = tour.departures.all().order_by('departure_date')
        return Response(TourDepartureSerializer(deps, many=True).data)

    payload = request.data.copy()
    payload['tour'] = tour.id
    serializer = TourDepartureSerializer(data=payload)
    if serializer.is_valid():
        dep = serializer.save(tour=tour)
        return Response(TourDepartureSerializer(dep).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH', 'DELETE'])
def admin_tour_departure_detail(request, departure_id):
    denied = require_admin(request)
    if denied: return denied
    departure = get_object_or_404(TourDeparture, pk=departure_id)
    if request.method == 'DELETE':
        departure.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    if 'is_cancelled' in request.data:
        departure.is_cancelled = bool(request.data['is_cancelled'])
    if 'slots_total' in request.data:
        try:
            departure.slots_total = int(request.data['slots_total'])
        except (ValueError, TypeError):
            return Response({'error': 'slots_total không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)
    if 'departure_date' in request.data:
        departure.departure_date = request.data['departure_date']
    departure.save()
    return Response(TourDepartureSerializer(departure).data)


@api_view(['GET'])
def admin_tour_bookings(request):
    denied = require_admin(request)
    if denied: return denied
    bookings = TourBooking.objects.select_related('departure__tour', 'user').order_by('-created_at')
    return Response(TourBookingSerializer(bookings, many=True, context={'request': request}).data)


@api_view(['PATCH'])
def admin_tour_booking_status(request, booking_id):
    denied = require_admin(request)
    if denied: return denied
    booking = get_object_or_404(TourBooking, pk=booking_id)
    next_status = request.data.get('status')
    if next_status not in ['pending', 'confirmed', 'cancelled']:
        return Response({'error': 'Trạng thái không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)

    if next_status == 'cancelled':
        booking, ok, error = _cancel_booking(
            booking,
            is_tour=True,
            is_admin=True,
            requested_refund=request.data.get('refund_amount', 0),
        )
        if not ok:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
    else:
        booking.status = next_status
        booking.save(update_fields=['status'])
    if next_status == 'confirmed':
        _record_confirmed_booking_feedback(booking, is_tour=True)
    return Response(TourBookingSerializer(booking, context={'request': request}).data)


@api_view(['POST'])
def booking_create(request):
    if not request.user.is_authenticated:
        return Response({'detail': 'Vui lòng đăng nhập để đặt phòng.'}, status=status.HTTP_401_UNAUTHORIZED)
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
        booking = serializer.save(user=request.user)

    return Response(BookingSerializer(booking, context={'request': request}).data, status=status.HTTP_201_CREATED)


def _momo_sign(secret_key, raw_signature):
    return hmac.new(secret_key.encode('utf-8'), raw_signature.encode('utf-8'), hashlib.sha256).hexdigest()


def _momo_callback_signature(access_key, payload):
    fields = ('amount', 'extraData', 'message', 'orderId', 'orderInfo', 'orderType', 'partnerCode', 'payType', 'requestId', 'responseTime', 'resultCode', 'transId')
    raw_signature = '&'.join(f'{field}={payload.get(field, "")}' for field in fields)
    return f'accessKey={access_key}&{raw_signature}'


def _momo_callback_signature_is_valid(access_key, secret_key, payload):
    signature = str(payload.get('signature') or '')
    if not signature:
        return False
    expected = _momo_sign(secret_key, _momo_callback_signature(access_key, payload))
    return hmac.compare_digest(signature, expected)


def _record_confirmed_booking_feedback(booking, is_tour):
    """Ghi nhận booked cho điểm đến của đơn đã thanh toán, không làm hỏng callback nếu lỗi."""
    try:
        destination = None
        if is_tour:
            tour = getattr(booking, 'tour', None) or (booking.departure.tour if getattr(booking, 'departure_id', None) else None)
            if tour:
                stop = tour.stops.select_related('destination').order_by('day_number').first()
                destination = stop.destination if stop else None
        else:
            destination = getattr(getattr(booking.room_type, 'accommodation', None), 'destination', None)
            if not destination and getattr(booking.room_type, 'accommodation', None):
                acc = booking.room_type.accommodation
                if acc.latitude and acc.longitude:
                    destinations = list(Destination.objects.all())
                    if destinations:
                        destination = min(destinations, key=lambda d: _haversine_km(acc.latitude, acc.longitude, d.latitude, d.longitude))
        if destination:
            record_booked_feedback(booking.user, destination)
        else:
            logger.warning('Không thể ghi feedback booked: đơn %s không xác định được điểm đến.', booking.id)
    except Exception as exc:
        logger.warning('Không thể ghi feedback booked cho đơn %s: %s', booking.id, exc)



def _apply_payment_result(booking, is_tour, success, transaction_id='', cancel_on_failure=True):
    """Apply a provider result once for return, IPN, and simulated payments."""
    was_confirmed = booking.status == 'confirmed'
    update_fields = []
    if success:
        if not was_confirmed:
            booking.status = 'confirmed'
            update_fields.append('status')
        if transaction_id and booking.momo_trans_id != str(transaction_id):
            booking.momo_trans_id = str(transaction_id)
            update_fields.append('momo_trans_id')
        if transaction_id and hasattr(booking, 'payment_transaction_id') and booking.payment_transaction_id != str(transaction_id):
            booking.payment_transaction_id = str(transaction_id)
            update_fields.append('payment_transaction_id')
        if update_fields:
            booking.save(update_fields=update_fields)
        if not was_confirmed:
            _record_confirmed_booking_feedback(booking, is_tour)
            if not is_tour and getattr(booking.user, 'email', None):
                try:
                    send_mail(
                        'Xác nhận đặt phòng thành công',
                        f'Xin chào {booking.user.username}, đặt phòng của bạn đã được xác nhận cho {booking.room_type.name} từ {booking.check_in} đến {booking.check_out}.',
                        settings.EMAIL_HOST_USER if hasattr(settings, 'EMAIL_HOST_USER') else 'noreply@example.com',
                        [booking.user.email],
                        fail_silently=True,
                    )
                except Exception as exc:
                    logger.warning('Không gửi được email xác nhận đơn %s: %s', booking.pk, exc)
    elif cancel_on_failure and booking.status != 'cancelled':
        booking.status = 'cancelled'
        booking.save(update_fields=['status'])
    return booking


def _vnpay_signature(secret, raw_data):
    return hmac.new(secret.encode('utf-8'), raw_data.encode('utf-8'), hashlib.sha512).hexdigest()


def _vnpay_query_string(params):
    return urlencode(sorted(params.items()))


def _vnpay_signature_is_valid(params, secret):
    received = str(params.get('vnp_SecureHash') or '')
    signed_params = {
        key: value for key, value in params.items()
        if key.startswith('vnp_') and key not in ('vnp_SecureHash', 'vnp_SecureHashType')
    }
    return bool(received and secret and hmac.compare_digest(
        received.lower(), _vnpay_signature(secret, _vnpay_query_string(signed_params)).lower(),
    ))


def _vnpay_booking_from_ref(txn_ref):
    match = re.fullmatch(r'(BOOK|TOUR)(\d+)X\d{14}[0-9a-f]{8}', str(txn_ref or ''))
    if not match:
        return None, None
    return (TourBooking if match.group(1) == 'TOUR' else Booking), int(match.group(2))


def _process_vnpay_callback(params):
    secret = os.getenv('VNPAY_HASH_SECRET', '')
    tmn_code = os.getenv('VNPAY_TMN_CODE', '')
    if not _vnpay_signature_is_valid(params, secret):
        return '97', None, False
    if not tmn_code or params.get('vnp_TmnCode') != tmn_code:
        return '97', None, False
    model_cls, booking_id = _vnpay_booking_from_ref(params.get('vnp_TxnRef'))
    if not model_cls:
        return '01', None, False
    try:
        booking = model_cls.objects.get(pk=booking_id)
    except model_cls.DoesNotExist:
        return '01', None, False
    if booking.payment_provider != 'vnpay' or booking.payment_order_ref != params.get('vnp_TxnRef'):
        return '01', booking, False
    is_tour = model_cls is TourBooking
    expected_amount = int(booking.total_price) if is_tour else int(
        booking.room_type.base_price * (booking.check_out - booking.check_in).days
    )
    try:
        callback_amount = int(params.get('vnp_Amount', '0'))
    except (TypeError, ValueError):
        return '04', booking, False
    if callback_amount != expected_amount * 100:
        return '04', booking, False
    if not params.get('vnp_TransactionNo') or not params.get('vnp_ResponseCode') or not params.get('vnp_TransactionStatus'):
        return '99', booking, False
    if booking.status == 'confirmed':
        return '02', booking, True

    success = params.get('vnp_ResponseCode') == '00' and params.get('vnp_TransactionStatus') == '00'
    with transaction.atomic():
        booking = model_cls.objects.select_for_update().get(pk=booking.pk)
        was_confirmed = booking.status == 'confirmed'
        if not was_confirmed:
            booking = _apply_payment_result(
                booking, is_tour, success,
                transaction_id=params.get('vnp_TransactionNo') or '',
                cancel_on_failure=False,
            )
        if success:
            booking.payment_provider = 'vnpay'
            booking.payment_transaction_id = str(params.get('vnp_TransactionNo') or '')
            booking.payment_pay_date = str(params.get('vnp_PayDate') or '')
            booking.save(update_fields=['payment_provider', 'payment_transaction_id', 'payment_pay_date'])
    return ('00' if success else '00'), booking, success


@api_view(['POST'])
def payment_init(request):
    if not request.user.is_authenticated:
        return Response({'detail': 'Vui lòng đăng nhập để thanh toán.'}, status=status.HTTP_401_UNAUTHORIZED)
    booking_id = request.data.get('booking_id')
    booking_type = request.data.get('booking_type', 'accommodation_booking')
    selected_provider = str(request.data.get('provider') or settings.PAYMENT_PROVIDER).strip().lower()
    if selected_provider not in ('momo', 'vnpay', 'simulated'):
        return Response({'error': 'Vui lòng chọn MoMo hoặc VNPay.'}, status=status.HTTP_400_BAD_REQUEST)
    if selected_provider == 'simulated' and settings.PAYMENT_PROVIDER != 'simulated':
        return Response({'error': 'Thanh toán mô phỏng hiện không được bật.'}, status=status.HTTP_404_NOT_FOUND)
    return_url = request.data.get('return_url') or 'http://localhost:5173/payment-return'

    is_tour = booking_type in ('tour_booking', 'tour')
    model_cls = TourBooking if is_tour else Booking
    try:
        booking = model_cls.objects.get(pk=booking_id)
    except (Booking.DoesNotExist, TourBooking.DoesNotExist):
        return Response({'error': 'Không tìm thấy đơn đặt chỗ.'}, status=status.HTTP_404_NOT_FOUND)

    if not (request.user.is_staff or request.user.is_superuser or booking.user_id == request.user.id):
        return Response({'detail': 'Bạn không có quyền thanh toán đơn này.'}, status=status.HTTP_403_FORBIDDEN)
    if booking.status == 'cancelled':
        return Response({'error': 'Đơn đã hủy không thể thanh toán.'}, status=status.HTTP_400_BAD_REQUEST)

    expected_amount = int(booking.total_price) if is_tour else int(
        booking.room_type.base_price * (booking.check_out - booking.check_in).days
    )

    # The server owns the payable amount; never trust a client-provided amount.
    amount_value = expected_amount
    if amount_value <= 0:
        return Response({'error': 'Số tiền thanh toán phải lớn hơn 0.'}, status=status.HTTP_400_BAD_REQUEST)

    order_type_str = 'tour_booking' if is_tour else 'accommodation_booking'
    if selected_provider == 'simulated':
        order_code = f"{'TOUR' if is_tour else 'BOOK'}-{booking.id}"
        return Response({
            'booking_id': booking.id,
            'booking_type': order_type_str,
            'amount': amount_value,
            'status': 'pending',
            'provider': 'simulated',
            'redirect_url': f'{settings.FRONTEND_URL.rstrip("/")}/thanh-toan-mo-phong?order={order_code}',
            'message': 'Đã tạo phiên thanh toán mô phỏng.',
        })

    ref_str = f'TOUR-{booking.id}' if is_tour else f'BOOK-{booking.id}'
    order_info = f'TourBooking_{booking.id}' if is_tour else f'Booking_{booking.id}'

    if selected_provider == 'vnpay':
        tnm_code = os.getenv('VNPAY_TMN_CODE', '')
        hash_secret = os.getenv('VNPAY_HASH_SECRET', '')
        if not (tnm_code and hash_secret):
            logger.error('VNPay payment_init rejected: VNPAY_TMN_CODE or VNPAY_HASH_SECRET is not configured.')
            return Response({'error': 'Chưa cấu hình thông tin kết nối VNPay Sandbox.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        create_date = timezone.localtime().strftime('%Y%m%d%H%M%S')
        txn_prefix = f'TOUR{booking.id}' if is_tour else f'BOOK{booking.id}'
        txn_ref = f'{txn_prefix}X{create_date}{uuid.uuid4().hex[:8]}'
        base_url = getattr(settings, 'BASE_URL', '').rstrip('/')
        callback_url = f'{base_url}/api/payments/return/' if base_url else request.build_absolute_uri('/api/payments/return/')
        params = {
            'vnp_Version': '2.1.0',
            'vnp_Command': 'pay',
            'vnp_TmnCode': tnm_code,
            'vnp_Amount': str(amount_value * 100),
            'vnp_CreateDate': create_date,
            'vnp_CurrCode': 'VND',
            'vnp_IpAddr': request.META.get('REMOTE_ADDR', '127.0.0.1'),
            'vnp_Locale': 'vn',
            'vnp_OrderInfo': order_info,
            'vnp_OrderType': 'other',
            'vnp_ReturnUrl': callback_url,
            'vnp_TxnRef': txn_ref,
        }
        signature = _vnpay_signature(hash_secret, _vnpay_query_string(params))
        redirect_url = f'https://sandbox.vnpayment.vn/paymentv2/vpcpay.html?{_vnpay_query_string(params)}&vnp_SecureHash={signature}'
        booking.payment_provider = 'vnpay'
        booking.payment_order_ref = txn_ref
        booking.payment_create_date = create_date
        booking.save(update_fields=['payment_provider', 'payment_order_ref', 'payment_create_date'])
        return Response({
            'booking_id': booking.id,
            'booking_type': order_type_str,
            'amount': amount_value,
            'status': 'pending',
            'provider': 'vnpay',
            'order_id': txn_ref,
            'redirect_url': redirect_url,
            'message': 'Đã tạo liên kết thanh toán VNPay Sandbox.',
        })

    momo_partner_code = os.getenv('MOMO_PARTNER_CODE')
    momo_access_key = os.getenv('MOMO_ACCESS_KEY')
    momo_secret_key = os.getenv('MOMO_SECRET_KEY')
    if not (momo_partner_code and momo_access_key and momo_secret_key):
        return Response({'error': 'Chưa cấu hình thông tin kết nối MoMo Sandbox.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    if momo_partner_code and momo_access_key and momo_secret_key:
        request_id = f'{ref_str}-{uuid.uuid4().hex[:20]}'
        order_id = f'{ref_str}-{uuid.uuid4().hex[:20]}'
        base_url = getattr(settings, 'BASE_URL', '').rstrip('/')
        momo_redirect_url = f'{base_url}/api/payments/return/' if base_url else request.build_absolute_uri('/api/payments/return/')
        momo_ipn_url = f'{base_url}/api/payments/momo/ipn/' if base_url else request.build_absolute_uri('/api/payments/momo/ipn/')
        extra_data = base64.b64encode(json.dumps({
            'booking_id': booking.id,
            'booking_type': order_type_str,
            'amount': amount_value,
            'client_return_url': return_url,
        }, separators=(',', ':')).encode('utf-8')).decode('ascii')
        booking.payment_provider = 'momo'
        booking.payment_order_ref = order_id
        booking.save(update_fields=['payment_provider', 'payment_order_ref'])
        request_type = 'payWithMethod'
        raw_signature = (
            f'accessKey={momo_access_key}&amount={amount_value}&extraData={extra_data}'
            f'&ipnUrl={momo_ipn_url}&orderId={order_id}&orderInfo={order_info}'
            f'&partnerCode={momo_partner_code}&redirectUrl={momo_redirect_url}'
            f'&requestId={request_id}&requestType={request_type}'
        )
        payload = {
            'partnerCode': momo_partner_code,
            'partnerName': 'Du Lich Thong Minh',
            'storeId': 'DuLichThongMinh',
            'requestId': request_id,
            'amount': amount_value,
            'orderId': order_id,
            'orderInfo': order_info,
            'redirectUrl': momo_redirect_url,
            'ipnUrl': momo_ipn_url,
            'requestType': request_type,
            'extraData': extra_data,
            'lang': 'vi',
            'autoCapture': True,
            'signature': _momo_sign(momo_secret_key, raw_signature),
        }
        try:
            momo_response = requests.post(
                'https://test-payment.momo.vn/v2/gateway/api/create',
                json=payload,
                timeout=10,
            )
            momo_response.raise_for_status()
            momo_body = momo_response.json()
        except (requests.RequestException, ValueError) as exc:
            logger.warning('MoMo create-payment API failed: %s', exc)
            return Response({'error': 'Cổng MoMo Sandbox hiện chưa tạo được giao dịch.'}, status=status.HTTP_502_BAD_GATEWAY)
        else:
            pay_url = momo_body.get('payUrl')
            if momo_body.get('resultCode') == 0 and pay_url:
                return Response({
                    'booking_id': booking.id,
                    'booking_type': order_type_str,
                    'amount': amount_value,
                    'status': 'pending',
                    'provider': 'momo',
                    'order_id': order_id,
                    'payUrl': pay_url,
                    'redirect_url': pay_url,
                    'message': momo_body.get('message', 'Đã tạo giao dịch MoMo.'),
                })
            logger.warning('MoMo create-payment rejected resultCode=%s message=%s', momo_body.get('resultCode'), momo_body.get('message'))
            return Response({'error': 'MoMo Sandbox từ chối khởi tạo giao dịch.'}, status=status.HTTP_502_BAD_GATEWAY)

    return Response({'error': 'Không thể khởi tạo thanh toán với nhà cung cấp hiện tại.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(['GET', 'POST'])
def simulated_payment_complete(request):
    if settings.PAYMENT_PROVIDER != 'simulated':
        return Response({'error': 'Thanh toán mô phỏng hiện không được bật.'}, status=status.HTTP_404_NOT_FOUND)
    if request.method == 'GET':
        return Response({'enabled': True})
    if not request.user.is_authenticated:
        return Response({'detail': 'Vui lòng đăng nhập để hoàn tất thanh toán.'}, status=status.HTTP_401_UNAUTHORIZED)

    order_code = str(request.data.get('order') or '').strip()
    result = request.data.get('result')
    parts = order_code.split('-')
    if len(parts) != 2 or parts[0] not in {'BOOK', 'TOUR'} or not parts[1].isdigit():
        return Response({'error': 'Mã đơn thanh toán không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)
    if result not in {'success', 'failed'}:
        return Response({'error': 'Kết quả chỉ có thể là success hoặc failed.'}, status=status.HTTP_400_BAD_REQUEST)

    is_tour = parts[0] == 'TOUR'
    model_cls = TourBooking if is_tour else Booking
    relation = 'departure__tour' if is_tour else 'room_type'
    try:
        booking = model_cls.objects.select_related('user', relation).get(pk=int(parts[1]))
    except model_cls.DoesNotExist:
        return Response({'error': 'Không tìm thấy đơn đặt chỗ.'}, status=status.HTTP_404_NOT_FOUND)
    if not (request.user.is_staff or request.user.is_superuser or booking.user_id == request.user.id):
        return Response({'detail': 'Bạn không có quyền hoàn tất đơn này.'}, status=status.HTTP_403_FORBIDDEN)
    if booking.status == 'cancelled':
        return Response({'error': 'Đơn đã hủy không thể thanh toán.'}, status=status.HTTP_400_BAD_REQUEST)

    succeeded = result == 'success'
    transaction_id = f'SIM-{uuid.uuid4().hex}' if succeeded else ''
    booking = _apply_payment_result(booking, is_tour, succeeded, transaction_id, cancel_on_failure=True)
    if succeeded:
        booking.payment_provider = 'simulated'
        booking.payment_transaction_id = transaction_id
        booking.payment_order_ref = order_code
        booking.save(update_fields=['payment_provider', 'payment_transaction_id', 'payment_order_ref'])
    return Response({
        'success': succeeded,
        'booking_id': booking.id,
        'booking_type': 'tour_booking' if is_tour else 'accommodation_booking',
        'order_id': order_code,
        'provider': 'simulated',
        'status': booking.status,
        'message': 'Thanh toán mô phỏng thành công.' if succeeded else 'Thanh toán mô phỏng thất bại.',
    })


@api_view(['GET'])
def payment_return(request):
    if any(key.startswith('vnp_') for key in request.GET):
        params = {key: value for key, value in request.GET.items() if key.startswith('vnp_')}
        response_code, booking, succeeded = _process_vnpay_callback(params)
        if response_code not in ('00', '02'):
            logger.warning('VNPay return rejected txn_ref=%s RspCode=%s', params.get('vnp_TxnRef'), response_code)
        redirect_query = urlencode({
            'provider': 'vnpay',
            'status': 'success' if succeeded else 'failed',
            'order': params.get('vnp_TxnRef', ''),
        })
        return HttpResponseRedirect(f'{settings.FRONTEND_URL.rstrip("/")}/payment-return?{redirect_query}')

    momo_order_id = request.GET.get('orderId')
    momo_signature = request.GET.get('signature')
    momo_access_key = os.getenv('MOMO_ACCESS_KEY')
    momo_secret_key = os.getenv('MOMO_SECRET_KEY')
    if momo_order_id or momo_signature:
        if not (momo_access_key and momo_secret_key and momo_order_id and momo_signature):
            return Response({'success': False, 'error': 'Thiếu dữ liệu hoặc cấu hình để xác thực callback MoMo.'}, status=status.HTTP_400_BAD_REQUEST)

        callback_payload = {key: request.GET.get(key, '') for key in (
            'amount', 'extraData', 'message', 'orderId', 'orderInfo', 'orderType',
            'partnerCode', 'payType', 'requestId', 'responseTime', 'resultCode', 'transId',
        )}
        callback_payload['signature'] = momo_signature
        if not _momo_callback_signature_is_valid(momo_access_key, momo_secret_key, callback_payload):
            logger.warning('payment_return: invalid MoMo callback signature for orderId=%s.', momo_order_id)
            return Response({'success': False, 'error': 'Chữ ký callback MoMo không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)
        if callback_payload['partnerCode'] != os.getenv('MOMO_PARTNER_CODE'):
            return Response({'success': False, 'error': 'partnerCode callback MoMo không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)

        booking_id = None
        booking_type = None
        expected_amount = None

        if callback_payload.get('extraData'):
            try:
                payment_context = json.loads(base64.b64decode(callback_payload['extraData']).decode('utf-8'))
                booking_id = int(payment_context.get('booking_id'))
                booking_type = payment_context.get('booking_type')
                expected_amount = int(payment_context.get('amount'))
            except (KeyError, TypeError, ValueError, UnicodeDecodeError) as exc:
                logger.warning('payment_return: could not parse extraData for orderId=%s: %s', momo_order_id, exc)

        if not booking_id:
            parts = momo_order_id.split('-')
            if len(parts) >= 2 and parts[1].isdigit():
                booking_id = int(parts[1])
                booking_type = 'tour_booking' if parts[0].upper() == 'TOUR' else 'accommodation_booking'

        if not booking_id:
            return Response({'success': False, 'error': 'Dữ liệu callback MoMo không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            callback_amount = int(callback_payload.get('amount', 0))
        except (TypeError, ValueError):
            return Response({'success': False, 'error': 'Số tiền callback MoMo không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)

        if expected_amount is not None and callback_amount != expected_amount:
            return Response({'success': False, 'error': 'Số tiền callback MoMo không khớp.'}, status=status.HTTP_400_BAD_REQUEST)

        is_tour = booking_type in ('tour_booking', 'tour')
        model_cls = TourBooking if is_tour else Booking
        try:
            booking = model_cls.objects.get(pk=booking_id)
        except (Booking.DoesNotExist, TourBooking.DoesNotExist):
            return Response({'success': False, 'error': 'Không tìm thấy đơn đặt chỗ.'}, status=status.HTTP_404_NOT_FOUND)

        if str(callback_payload.get('resultCode', '')).strip() == '0':
            booking.payment_provider = 'momo'
            booking.payment_order_ref = momo_order_id
            booking.save(update_fields=['payment_provider', 'payment_order_ref'])
            booking = _apply_payment_result(booking, is_tour, True, callback_payload.get('transId') or '')
            callback_message = callback_payload.get('message') or ''
            callback_message = {'Successful.': 'Thanh toán thành công.'}.get(callback_message, callback_message or 'Thanh toán MoMo thành công.')
            return Response({
                'success': True,
                'booking_id': booking.id,
                'booking_type': 'tour_booking' if is_tour else 'accommodation_booking',
                'order_id': momo_order_id,
                'provider': 'momo',
                'status': booking.status,
                'message': callback_message,
            })

        booking.payment_provider = 'momo'
        booking.payment_order_ref = momo_order_id
        booking.save(update_fields=['payment_provider', 'payment_order_ref'])
        _apply_payment_result(booking, is_tour, False)
        callback_message = callback_payload.get('message') or ''
        callback_message = {'Transaction failed.': 'Giao dịch không thành công.'}.get(callback_message, callback_message or 'Thanh toán MoMo không thành công.')
        return Response({
            'success': False,
            'booking_id': booking.id,
            'booking_type': 'tour_booking' if is_tour else 'accommodation_booking',
            'order_id': momo_order_id,
            'provider': 'momo',
            'status': booking.status,
            'resultCode': callback_payload['resultCode'],
            'message': callback_message,
        }, status=status.HTTP_400_BAD_REQUEST)

    booking_id = request.GET.get('booking_id')
    booking_type = request.GET.get('booking_type', 'accommodation_booking')
    status_value = request.GET.get('status', 'failed')

    is_tour = booking_type in ('tour_booking', 'tour')
    model_cls = TourBooking if is_tour else Booking
    try:
        booking = model_cls.objects.get(pk=booking_id)
    except (Booking.DoesNotExist, TourBooking.DoesNotExist):
        return Response({'success': False, 'error': 'Không tìm thấy đơn đặt chỗ.'}, status=status.HTTP_404_NOT_FOUND)

    if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser or booking.user_id == request.user.id):
        return Response({'success': False, 'error': 'Bạn không có quyền xem kết quả đơn này.'}, status=status.HTTP_403_FORBIDDEN)

    if status_value == 'success':
        booking = _apply_payment_result(booking, is_tour, True)
        return Response({
            'success': True,
            'booking_id': booking.id,
            'booking_type': 'tour_booking' if is_tour else 'accommodation_booking',
            'status': booking.status,
            'message': 'Thanh toán thành công. Đơn đặt chỗ đã được xác nhận.',
        })

    _apply_payment_result(booking, is_tour, False)
    return Response({
        'success': False,
        'booking_id': booking.id,
        'booking_type': 'tour_booking' if is_tour else 'accommodation_booking',
        'status': booking.status,
        'message': 'Thanh toán thất bại hoặc bị hủy.',
    }, status=status.HTTP_400_BAD_REQUEST)


def _call_momo_refund(booking, refund_amount, is_tour=False):
    """Submit a sandbox refund using MoMo's documented canonical HMAC string."""
    if booking.payment_provider == 'vnpay':
        return _call_vnpay_refund(booking, refund_amount, is_tour)
    if str(booking.momo_trans_id or '').startswith('SIM-'):
        booking.refund_status = 'refunded'
        booking.refunded_at = timezone.now()
        booking.save(update_fields=['refund_status', 'refunded_at'])
        logger.info(
            'Hoàn tiền mô phỏng: booking_type=%s booking_id=%s amount=%s; không gọi API MoMo.',
            'tour' if is_tour else 'room', booking.pk, refund_amount,
        )
        return
    if not booking.momo_trans_id:
        booking.refund_status = 'refunded'
        booking.refunded_at = timezone.now()
        booking.save(update_fields=['refund_status', 'refunded_at'])
        logger.info('Refund simulated: booking_type=%s booking_id=%s amount=%s; no MoMo transaction id.', 'tour' if is_tour else 'room', booking.pk, refund_amount)
        return
    if refund_amount <= 0:
        booking.refund_status = 'refunded'
        booking.refunded_at = timezone.now()
        booking.save(update_fields=['refund_status', 'refunded_at'])
        logger.info('MoMo refund not requested for zero amount: booking_id=%s.', booking.pk)
        return

    partner_code = os.getenv('MOMO_PARTNER_CODE', '')
    access_key = os.getenv('MOMO_ACCESS_KEY', '')
    secret_key = os.getenv('MOMO_SECRET_KEY', '')
    booking.refund_status = 'pending'
    booking.refunded_at = None
    booking.save(update_fields=['refund_status', 'refunded_at'])
    request_id = uuid.uuid4().hex
    refund_order_id = f"REF-{'TOUR' if is_tour else 'BOOK'}-{booking.pk}-{request_id[:12]}"
    description = f"Hoàn tiền đơn {'tour' if is_tour else 'phòng'} {booking.pk}"
    try:
        if not (partner_code and access_key and secret_key):
            raise RuntimeError('Thiếu cấu hình MOMO_PARTNER_CODE, MOMO_ACCESS_KEY hoặc MOMO_SECRET_KEY.')
        trans_id = int(booking.momo_trans_id)
        canonical = (
            f'accessKey={access_key}&amount={refund_amount}&description={description}'
            f'&orderId={refund_order_id}&partnerCode={partner_code}&requestId={request_id}'
            f'&transId={trans_id}'
        )
        payload = {
            'partnerCode': partner_code,
            'orderId': refund_order_id,
            'requestId': request_id,
            'amount': int(refund_amount),
            'transId': trans_id,
            'lang': 'vi',
            'description': description,
            'signature': _momo_sign(secret_key, canonical),
        }
        response = requests.post('https://test-payment.momo.vn/v2/gateway/api/refund', json=payload, timeout=30)
        response.raise_for_status()
        body = response.json()
        if int(body.get('resultCode', -1)) != 0:
            raise RuntimeError(f"MoMo từ chối hoàn tiền resultCode={body.get('resultCode')}, message={body.get('message')}")
    except Exception as exc:
        booking.refund_status = 'failed'
        booking.save(update_fields=['refund_status'])
        logger.exception('MoMo refund failed: booking_type=%s booking_id=%s amount=%s reason=%s', 'tour' if is_tour else 'room', booking.pk, refund_amount, exc)
        return
    booking.refund_status = 'refunded'
    booking.refunded_at = timezone.now()
    booking.save(update_fields=['refund_status', 'refunded_at'])
    logger.info('MoMo refund succeeded: booking_type=%s booking_id=%s amount=%s refund_order_id=%s', 'tour' if is_tour else 'room', booking.pk, refund_amount, refund_order_id)


def _call_vnpay_refund(booking, refund_amount, is_tour=False):
    """Gửi yêu cầu hoàn VNPay sandbox với chuỗi ký HMAC-SHA512 chính thức."""
    tmn_code = os.getenv('VNPAY_TMN_CODE', '')
    secret = os.getenv('VNPAY_HASH_SECRET', '')
    request_id = uuid.uuid4().hex[:32]
    create_date = timezone.localtime().strftime('%Y%m%d%H%M%S')
    transaction_date = booking.payment_create_date
    transaction_ref = booking.payment_order_ref
    transaction_id = booking.payment_transaction_id or booking.momo_trans_id
    expected_amount = int(booking.total_price) if is_tour else int(
        booking.room_type.base_price * (booking.check_out - booking.check_in).days
    )
    transaction_type = '02' if refund_amount >= expected_amount else '03'
    order_info = f'Hoan tien don {"tour" if is_tour else "phong"} {booking.pk}'
    values = [
        request_id, '2.1.0', 'refund', tmn_code, transaction_type, transaction_ref,
        str(int(refund_amount) * 100), str(transaction_id), transaction_date,
        str(booking.user.username)[:245], create_date, '127.0.0.1', order_info,
    ]
    booking.refund_status = 'pending'
    booking.refunded_at = None
    booking.save(update_fields=['refund_status', 'refunded_at'])
    try:
        if not all((tmn_code, secret, transaction_ref, transaction_date, transaction_id)):
            raise RuntimeError('Thiếu dữ liệu giao dịch hoặc cấu hình VNPay để hoàn tiền.')
        payload = {
            'vnp_RequestId': request_id,
            'vnp_Version': '2.1.0',
            'vnp_Command': 'refund',
            'vnp_TmnCode': tmn_code,
            'vnp_TransactionType': transaction_type,
            'vnp_TxnRef': transaction_ref,
            'vnp_Amount': str(int(refund_amount) * 100),
            'vnp_TransactionNo': str(transaction_id),
            'vnp_TransactionDate': transaction_date,
            'vnp_CreateBy': str(booking.user.username)[:245],
            'vnp_CreateDate': create_date,
            'vnp_IpAddr': '127.0.0.1',
            'vnp_OrderInfo': order_info,
        }
        payload['vnp_SecureHash'] = _vnpay_signature(secret, '|'.join(values))
        response = requests.post(
            'https://sandbox.vnpayment.vn/merchant_webapi/api/transaction',
            json=payload,
            timeout=20,
        )
        response.raise_for_status()
        body = response.json()
        if str(body.get('vnp_ResponseCode')) != '00':
            raise RuntimeError(f"VNPay từ chối hoàn tiền responseCode={body.get('vnp_ResponseCode')}, message={body.get('vnp_Message')}")
    except Exception as exc:
        booking.refund_status = 'failed'
        booking.save(update_fields=['refund_status'])
        logger.exception('VNPay refund failed: booking_type=%s booking_id=%s amount=%s reason=%s', 'tour' if is_tour else 'room', booking.pk, refund_amount, exc)
        return
    booking.refund_status = 'refunded'
    booking.refunded_at = timezone.now()
    booking.save(update_fields=['refund_status', 'refunded_at'])
    logger.info('VNPay refund succeeded: booking_type=%s booking_id=%s amount=%s request_id=%s', 'tour' if is_tour else 'room', booking.pk, refund_amount, request_id)


def _cancel_booking(booking, is_tour=False, is_admin=False, requested_refund=None):
    with transaction.atomic():
        model_cls = TourBooking if is_tour else Booking
        booking = model_cls.objects.select_for_update().select_related('user', 'departure__tour' if is_tour else 'room_type').get(pk=booking.pk)
        if booking.status == 'cancelled':
            return booking, True, ''
        was_paid = booking.status == 'confirmed'
        if is_admin:
            if was_paid:
                try:
                    refund_amount = max(0, int(requested_refund or 0))
                except (TypeError, ValueError):
                    return booking, False, 'Số tiền hoàn tùy chỉnh không hợp lệ.'
            else:
                refund_amount = 0
        else:
            preview = cancellation_refund_preview(booking, is_tour)
            if not preview['can_cancel']:
                return booking, False, preview['message']
            refund_amount = preview['refund_amount']
        booking.status = 'cancelled'
        booking.refund_amount = refund_amount
        booking.save(update_fields=['status', 'refund_amount'])
    if was_paid:
        _call_momo_refund(booking, refund_amount, is_tour)
    booking.refresh_from_db()
    return booking, True, ''


@api_view(['GET'])
def my_bookings(request):
    if not request.user.is_authenticated:
        return Response({'detail': 'Vui lòng đăng nhập để xem đơn đặt chỗ.'}, status=status.HTTP_401_UNAUTHORIZED)
    room_bookings = Booking.objects.select_related('user', 'room_type').filter(user=request.user).order_by('-created_at')
    tour_bookings = TourBooking.objects.select_related('user', 'departure__tour').filter(user=request.user).order_by('-created_at')
    rooms = BookingSerializer(room_bookings, many=True, context={'request': request}).data
    tours = TourBookingSerializer(tour_bookings, many=True, context={'request': request}).data
    reviewed_booking_ids = set(AccommodationReview.objects.filter(
        booking__user=request.user,
        booking__isnull=False,
    ).values_list('booking_id', flat=True))
    for item, booking in zip(rooms, room_bookings):
        item['can_cancel'] = item['refund_preview']['can_cancel']
        item['cancellation_refund_amount'] = item['refund_preview']['refund_amount']
        item['booking_kind'] = 'room'
        item['accommodation_id'] = booking.room_type.accommodation_id
        item['can_review'] = (
            booking.status == 'confirmed'
            and booking.check_out < timezone.localdate()
            and booking.pk not in reviewed_booking_ids
        )
    for item, booking in zip(tours, tour_bookings):
        item['can_cancel'] = item['refund_preview']['can_cancel']
        item['cancellation_refund_amount'] = item['refund_preview']['refund_amount']
        item['booking_kind'] = 'tour'
    return Response({'room_bookings': rooms, 'tour_bookings': tours})


@api_view(['POST'])
def booking_cancel(request, booking_id):
    try:
        booking = Booking.objects.select_related('user', 'room_type').get(pk=booking_id)
    except Booking.DoesNotExist:
        return Response({'error': 'Không tìm thấy đặt phòng.'}, status=status.HTTP_404_NOT_FOUND)
    is_admin = bool(request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser))
    if not is_admin and (not request.user.is_authenticated or booking.user_id != request.user.id):
        return Response({'detail': 'Bạn không có quyền hủy đơn này.'}, status=status.HTTP_403_FORBIDDEN)
    refund_input = request.data.get('refund_amount') if is_admin else None
    booking, ok, error = _cancel_booking(booking, is_admin=is_admin, requested_refund=refund_input)
    if not ok:
        return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
    return Response({
        'booking_id': booking.id,
        'status': booking.status,
        'refund_amount': int(booking.refund_amount),
        'refund_status': booking.refund_status,
        'refunded_at': booking.refunded_at,
        'message': 'Đơn đặt phòng đã được hủy.',
    })


@api_view(['POST'])
def tour_booking_cancel(request, booking_id):
    try:
        booking = TourBooking.objects.select_related('user', 'departure__tour').get(pk=booking_id)
    except TourBooking.DoesNotExist:
        return Response({'error': 'Không tìm thấy đơn đặt tour.'}, status=status.HTTP_404_NOT_FOUND)
    is_admin = bool(request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser))
    if not is_admin and (not request.user.is_authenticated or booking.user_id != request.user.id):
        return Response({'detail': 'Bạn không có quyền hủy đơn này.'}, status=status.HTTP_403_FORBIDDEN)
    refund_input = request.data.get('refund_amount') if is_admin else None
    booking, ok, error = _cancel_booking(booking, is_tour=True, is_admin=is_admin, requested_refund=refund_input)
    if not ok:
        return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
    return Response({
        'booking_id': booking.id,
        'status': booking.status,
        'refund_amount': int(booking.refund_amount),
        'refund_status': booking.refund_status,
        'refunded_at': booking.refunded_at,
        'message': 'Đơn đặt tour đã được hủy.',
    })


@api_view(['POST'])
def momo_ipn(request):
    """Receive and log MoMo server-to-server payment notifications."""
    payload = request.data if isinstance(request.data, dict) else {}
    order_id = str(payload.get('orderId') or '')
    logger.info('MoMo IPN received orderId=%s payload=%s', order_id, json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str))

    access_key = os.getenv('MOMO_ACCESS_KEY')
    secret_key = os.getenv('MOMO_SECRET_KEY')
    if not (access_key and secret_key and payload.get('signature')):
        logger.warning('MoMo IPN rejected: missing signing configuration/signature orderId=%s', order_id)
        return Response({'message': 'Chữ ký không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)
    if not _momo_callback_signature_is_valid(access_key, secret_key, payload):
        logger.warning('MoMo IPN rejected: invalid signature orderId=%s', order_id)
        return Response({'message': 'Chữ ký không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)
    if payload.get('partnerCode') != os.getenv('MOMO_PARTNER_CODE'):
        logger.warning('MoMo IPN rejected: partnerCode mismatch orderId=%s', order_id)
        return Response({'message': 'Mã đối tác không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        callback_amount = int(payload.get('amount'))
        result_code = int(payload.get('resultCode'))
    except (TypeError, ValueError):
        logger.warning('MoMo IPN rejected: invalid amount/resultCode orderId=%s', order_id)
        return Response({'message': 'Số tiền hoặc mã kết quả không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)

    booking_id = None
    booking_type = None
    expected_amount = None
    extra_data = payload.get('extraData') or ''
    if extra_data:
        try:
            payment_context = json.loads(base64.b64decode(extra_data).decode('utf-8'))
            booking_id = int(payment_context.get('booking_id'))
            booking_type = payment_context.get('booking_type')
            expected_amount = int(payment_context.get('amount'))
        except (KeyError, TypeError, ValueError, UnicodeDecodeError) as exc:
            logger.warning('MoMo IPN invalid extraData orderId=%s: %s', order_id, exc)
            return Response({'message': 'Dữ liệu bổ sung không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)
    if not booking_id:
        parts = order_id.split('-')
        if len(parts) >= 2 and parts[1].isdigit():
            booking_id = int(parts[1])
            booking_type = 'tour_booking' if parts[0].upper() == 'TOUR' else 'accommodation_booking'
    if not booking_id or (expected_amount is not None and callback_amount != expected_amount):
        logger.warning('MoMo IPN rejected: invalid booking or amount orderId=%s', order_id)
        return Response({'message': 'Đơn đặt chỗ hoặc số tiền không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)

    is_tour = booking_type in ('tour_booking', 'tour')
    model_cls = TourBooking if is_tour else Booking
    try:
        with transaction.atomic():
            booking = model_cls.objects.select_for_update().get(pk=booking_id)
            was_confirmed = booking.status == 'confirmed'
            booking.payment_provider = 'momo'
            booking.payment_order_ref = order_id
            booking.save(update_fields=['payment_provider', 'payment_order_ref'])
            if result_code == 0:
                booking = _apply_payment_result(
                    booking, is_tour, True, transaction_id=payload.get('transId') or '',
                )
            else:
                booking = _apply_payment_result(booking, is_tour, False, cancel_on_failure=False)
    except (Booking.DoesNotExist, TourBooking.DoesNotExist):
        logger.warning('MoMo IPN rejected: booking not found orderId=%s booking_id=%s', order_id, booking_id)
        return Response({'message': 'Không tìm thấy đơn đặt chỗ.'}, status=status.HTTP_404_NOT_FOUND)

    logger.info(
        'MoMo IPN processed orderId=%s resultCode=%s status=%s idempotent=%s',
        order_id, result_code, booking.status, result_code == 0 and was_confirmed,
    )
    # MoMo's Payment Notification API requires HTTP 204 with an empty body.
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
def vnpay_ipn(request):
    """Nhận IPN server-to-server của VNPay và trả mã phản hồi theo tài liệu."""
    params = {key: value for key, value in request.GET.items() if key.startswith('vnp_')}
    logger.info('VNPay IPN received txn_ref=%s', params.get('vnp_TxnRef', ''))
    if not params:
        return JsonResponse({'RspCode': '99', 'Message': 'Thiếu dữ liệu giao dịch.'})
    response_code, booking, succeeded = _process_vnpay_callback(params)
    message = {
        '00': 'Đã ghi nhận kết quả thanh toán.',
        '02': 'Giao dịch đã được xác nhận trước đó.',
        '01': 'Không tìm thấy giao dịch.',
        '04': 'Số tiền không hợp lệ.',
        '97': 'Chữ ký không hợp lệ.',
        '99': 'Không thể xử lý dữ liệu giao dịch.',
    }.get(response_code, 'Không thể xử lý dữ liệu giao dịch.')
    logger.info(
        'VNPay IPN processed txn_ref=%s rsp_code=%s booking_id=%s paid=%s',
        params.get('vnp_TxnRef', ''), response_code, getattr(booking, 'pk', None), succeeded,
    )
    return JsonResponse({'RspCode': response_code, 'Message': message})


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
            endpoint = 'https://api.openrouteservice.org/v2/directions/driving-car/geojson'
            headers = {'Authorization': ors_api_key, 'Content-Type': 'application/json'}
            route_request = {'coordinates': [[start_lng, start_lat], [end_lng, end_lat]]}
            response = requests.post(endpoint, headers=headers, json=route_request, timeout=10)
            if response.status_code == 404:
                logger.warning(
                    'route_planning: OpenRouteService returned 404 without radiuses; retrying with 10km snap radiuses.'
                )
                response = requests.post(
                    endpoint,
                    headers=headers,
                    json={**route_request, 'radiuses': [10000, 10000]},
                    timeout=10,
                )
            if response.status_code == 200:
                payload = response.json()
                feature = payload.get('features', [{}])[0]
                properties = feature.get('properties', {})
                segments = properties.get('segments', [])
                summary = segments[0] if segments else properties.get('summary', {})
                geometry = feature.get('geometry', {})
                # ORS returns GeoJSON coordinates as [longitude, latitude].
                route_geometry = [
                    [coordinate[1], coordinate[0]]
                    for coordinate in geometry.get('coordinates', [])
                    if isinstance(coordinate, list) and len(coordinate) >= 2
                ]
                if not route_geometry:
                    route_geometry = [[start_lat, start_lng], [end_lat, end_lng]]
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
                    'geometry': route_geometry,
                })
            logger.warning('route_planning fallback: OpenRouteService API returned status %s after route request; using Haversine estimate.', response.status_code)
        except requests.Timeout:
            logger.warning('route_planning fallback: OpenRouteService request timed out; using Haversine estimate.')
        except requests.RequestException as exc:
            logger.warning('route_planning fallback: OpenRouteService API request failed: %s; using Haversine estimate.', exc)
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            logger.warning('route_planning fallback: OpenRouteService response could not be processed: %s; using Haversine estimate.', exc)
    else:
        logger.warning('route_planning fallback: ORS_API_KEY is missing; using Haversine estimate.')

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
        # A safe visual fallback when ORS is unavailable. It intentionally has
        # only endpoints, so the UI can label it as an estimated direct route.
        'geometry': [[start_lat, start_lng], [end_lat, end_lng]],
    })


@api_view(['GET'])
def recommendation_explanation(request):
    query_params = request.GET
    preferences = query_params.get('user_preferences', '')
    weather_preference = query_params.get('weather_preference', 'balanced')
    if weather_preference not in WEATHER_PREFERENCES:
        return Response({'error': 'Lựa chọn thời tiết không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)
    budget_estimate = float(query_params.get('budget_estimate', 0) or 0)
    latitude = float(query_params['latitude']) if query_params.get('latitude') else None
    longitude = float(query_params['longitude']) if query_params.get('longitude') else None
    travel_date = query_params.get('travel_date')
    top_n = int(query_params.get('top_n', 5) or 5)

    try:
        travel_date = date.fromisoformat(travel_date) if travel_date else date.today()
    except ValueError:
        travel_date = date.today()

    destination_ids = [value for value in query_params.get('destination_ids', '').split(',') if value]
    selected_top_destination = None
    if destination_ids:
        try:
            numeric_ids = [int(value) for value in destination_ids]
        except ValueError:
            return Response({'error': 'Mã điểm đến không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)
        destinations = list(Destination.objects.filter(pk__in=numeric_ids))
        by_id = {destination.pk: destination for destination in destinations}
        if len(by_id) != len(set(numeric_ids)):
            return Response({'error': 'Một hoặc nhiều điểm đến không còn tồn tại.'}, status=status.HTTP_400_BAD_REQUEST)
        selected = by_id[numeric_ids[0]]
        selected_top_destination = DestinationSerializer(selected).data
        selected_top_destination['name'] = selected.name
        destination_data_raw = query_params.get('destination_data')
        if destination_data_raw:
            try:
                supplied_data = json.loads(destination_data_raw)
            except (TypeError, ValueError):
                return Response({'error': 'Dữ liệu điểm đến giải thích không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)
            if not isinstance(supplied_data, dict) or str(supplied_data.get('id')) != str(selected.pk):
                return Response({'error': 'Dữ liệu giải thích không khớp với điểm đến đã chọn.'}, status=status.HTTP_400_BAD_REQUEST)
            allowed_explanation_fields = (
                'criteria_used', 'preference_matched', 'preference_score', 'preference_raw',
                'weather_score', 'weather_available', 'weather', 'budget_score',
                'budget_overage', 'estimated_cost', 'distance_score', 'distance_km', 'score',
            )
            selected_top_destination.update({
                key: supplied_data[key] for key in allowed_explanation_fields if key in supplied_data
            })
        else:
            selected_weather = get_weather_score(
                selected.latitude, selected.longitude, travel_date, weather_preference,
            )
            selected_top_destination.update({
                'weather_score': selected_weather['weather_score'],
                'weather_available': selected_weather['weather_available'],
                'weather': selected_weather['weather'],
            })

    try:
        results = [selected_top_destination] if selected_top_destination else _recommendation_results(
            preferences, budget_estimate, latitude, longitude, travel_date, top_n,
            weather_preference=weather_preference,
        )
    except Exception as exc:
        return Response({'error': f'Không thể tạo gợi ý: {exc}'}, status=status.HTTP_502_BAD_GATEWAY)
    top_destination = results[0] if results else None

    from .tasks import generate_recommendation_explanation_task
    task = generate_recommendation_explanation_task.delay(
        preferences,
        budget_estimate,
        latitude,
        longitude,
        travel_date.isoformat(),
        top_destination,
        weather_preference,
    )
    return Response({'task_id': task.id, 'status': 'pending'}, status=status.HTTP_202_ACCEPTED)


@api_view(['GET'])
def task_status(request, task_id):
    """Kiểm tra trạng thái tiến trình Celery qua AsyncResult(task_id)."""
    from celery.result import AsyncResult
    from config.celery import app as celery_app
    result = AsyncResult(task_id, app=celery_app)
    state = result.state

    if state == 'SUCCESS':
        return Response({
            'status': 'done',
            'result': result.result,
        })
    elif state == 'FAILURE':
        return Response({
            'status': 'failed',
            'error': str(result.result),
        })
    else:
        return Response({
            'status': 'pending',
        })


@api_view(['GET'])
def weather_forecast(request):
    try:
        latitude = float(request.GET.get('latitude', 0) or 0)
        longitude = float(request.GET.get('longitude', 0) or 0)
        target_date = request.GET.get('date') or str(date.today())
        target_date = date.fromisoformat(target_date)
        weather_preference = request.GET.get('weather_preference', 'balanced')
        if weather_preference not in WEATHER_PREFERENCES:
            return Response({'error': 'Lựa chọn thời tiết không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)
    except ValueError:
        return Response({'error': 'latitude, longitude và date không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        return Response(get_weather_score(latitude, longitude, target_date, weather_preference))
    except Exception as exc:
        return Response({'error': f'Không thể lấy dữ liệu thời tiết: {exc}'}, status=status.HTTP_502_BAD_GATEWAY)


@api_view(['POST'])
def register_user(request):
    username = str(request.data.get('username') or '').strip()
    email = str(request.data.get('email') or '').strip()
    password = request.data.get('password') or ''

    if not username or not email or not password:
        return Response({'error': 'Tên đăng nhập, email và mật khẩu là bắt buộc.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        validate_email(email)
    except ValidationError:
        return Response({'error': 'Địa chỉ email không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)

    confirmation = request.data.get('password_confirm')
    if confirmation is not None and password != confirmation:
        return Response({'error': 'Hai mật khẩu chưa khớp.'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        return Response({'error': 'Tên đăng nhập đã tồn tại.'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(email__iexact=email).exists():
        return Response({'error': 'Email này đã được sử dụng.'}, status=status.HTTP_400_BAD_REQUEST)
    errors = password_errors(password, User(username=username, email=email))
    if errors:
        return Response({'error': ' '.join(errors), 'password_errors': errors}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(username=username, email=email, password=password)
    UserProfile.objects.get_or_create(user=user)
    login(request, user)

    return Response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'is_staff': user.is_staff or user.is_superuser,
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def login_user(request):
    username = str(request.data.get('username') or '').strip()
    password = request.data.get('password') or ''

    keys = [throttle_key('login', 'ip', request.META.get('REMOTE_ADDR') or 'unknown')]
    if username:
        keys.append(throttle_key('login', 'username', username))
    remaining = throttle_remaining(keys, 10)
    if remaining:
        response = Response({
            'error': f'Đăng nhập sai quá nhiều lần. Vui lòng thử lại sau {remaining} giây.',
            'retry_after_seconds': remaining,
        }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        response['Retry-After'] = str(remaining)
        return response

    user = authenticate(username=username, password=password)
    if user is None:
        record_attempt(keys, 10 * 60)
        return Response({'error': 'Tên đăng nhập hoặc mật khẩu không đúng.'}, status=status.HTTP_401_UNAUTHORIZED)

    login(request, user)
    profile = UserProfile.objects.filter(user=user).first()
    return Response({
        'success': True,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_staff': user.is_staff or user.is_superuser,
        },
        'profile': {
            'travel_preferences': profile.travel_preferences if profile else [],
            'budget_estimate': str(profile.budget_estimate) if profile else '0',
            'weather_preference': profile.weather_preference if profile else 'balanced',
            'free_text': profile.free_text if profile else '',
        },
    })


@api_view(['GET'])
def current_user(request):
    if not request.user.is_authenticated:
        return Response({'detail': 'Vui lòng đăng nhập để tiếp tục.'}, status=status.HTTP_401_UNAUTHORIZED)
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    return Response({
        'user': {
            'id': request.user.id,
            'username': request.user.username,
            'display_name': request.user.first_name or request.user.username,
            'email': request.user.email,
            'is_staff': request.user.is_staff or request.user.is_superuser,
        },
        'profile': {
            'travel_preferences': profile.travel_preferences,
            'budget_estimate': str(profile.budget_estimate),
            'weather_preference': profile.weather_preference,
            'free_text': profile.free_text,
        },
    })


@ensure_csrf_cookie
@api_view(['GET'])
def csrf_cookie(request):
    return Response({'detail': 'Đã thiết lập cookie bảo mật.', 'csrfToken': get_token(request)})


@api_view(['POST'])
def logout_user(request):
    logout(request)
    return Response({'success': True})


@api_view(['POST'])
def change_password(request):
    if not request.user.is_authenticated:
        return Response({'detail': 'Vui lòng đăng nhập để đổi mật khẩu.'}, status=status.HTTP_401_UNAUTHORIZED)
    user = request.user
    keys = [
        throttle_key('change-password', 'ip', request.META.get('REMOTE_ADDR') or 'unknown'),
        throttle_key('change-password', 'username', user.username),
    ]
    remaining = throttle_remaining(keys, 10)
    if remaining:
        response = Response({
            'error': f'Bạn đã nhập sai mật khẩu hiện tại quá nhiều lần. Vui lòng thử lại sau {remaining} giây.',
            'retry_after_seconds': remaining,
        }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        response['Retry-After'] = str(remaining)
        return response

    current_password = request.data.get('current_password') or ''
    new_password = request.data.get('new_password') or ''
    confirmation = request.data.get('new_password_confirm') or ''
    if not user.check_password(current_password):
        record_attempt(keys, 10 * 60)
        return Response({'error': 'Mật khẩu hiện tại không đúng.'}, status=status.HTTP_400_BAD_REQUEST)
    if new_password != confirmation:
        return Response({'error': 'Hai mật khẩu mới chưa khớp.'}, status=status.HTTP_400_BAD_REQUEST)
    errors = password_errors(new_password, user)
    if errors:
        return Response({'error': ' '.join(errors), 'password_errors': errors}, status=status.HTTP_400_BAD_REQUEST)
    user.set_password(new_password)
    user.save(update_fields=['password'])
    update_session_auth_hash(request, user)
    return Response({'message': 'Đã đổi mật khẩu. Phiên hiện tại được giữ lại.'})


@api_view(['PATCH'])
def account_detail(request):
    if not request.user.is_authenticated:
        return Response({'detail': 'Vui lòng đăng nhập để sửa tài khoản.'}, status=status.HTTP_401_UNAUTHORIZED)
    user = request.user
    if 'display_name' not in request.data and 'email' not in request.data:
        return Response({'error': 'Chưa có thông tin tài khoản để cập nhật.'}, status=status.HTTP_400_BAD_REQUEST)
    display_name = user.first_name
    if 'display_name' in request.data:
        display_name = str(request.data.get('display_name') or '').strip()
        if not display_name:
            return Response({'error': 'Tên hiển thị không được để trống.'}, status=status.HTTP_400_BAD_REQUEST)
        if len(display_name) > 150:
            return Response({'error': 'Tên hiển thị không được dài quá 150 ký tự.'}, status=status.HTTP_400_BAD_REQUEST)
    email = user.email
    if 'email' in request.data:
        email = str(request.data.get('email') or '').strip()
        try:
            validate_email(email)
        except ValidationError:
            return Response({'error': 'Địa chỉ email không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)
        if email != user.email:
            keys = [
                throttle_key('account-email', 'ip', request.META.get('REMOTE_ADDR') or 'unknown'),
                throttle_key('account-email', 'username', user.username),
            ]
            remaining = throttle_remaining(keys, 10)
            if remaining:
                response = Response({
                    'error': f'Bạn đã nhập sai mật khẩu hiện tại quá nhiều lần. Vui lòng thử lại sau {remaining} giây.',
                    'retry_after_seconds': remaining,
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
                response['Retry-After'] = str(remaining)
                return response
            if not user.check_password(request.data.get('current_password') or ''):
                record_attempt(keys, 10 * 60)
                return Response({'error': 'Cần nhập đúng mật khẩu hiện tại để đổi email.'}, status=status.HTTP_400_BAD_REQUEST)
            if User.objects.filter(email__iexact=email).exclude(pk=user.pk).exists():
                return Response({'error': 'Email này đã được sử dụng.'}, status=status.HTTP_400_BAD_REQUEST)
    user.first_name = display_name
    user.email = email
    user.save(update_fields=['first_name', 'email'])
    return Response({'id': user.pk, 'username': user.username, 'display_name': user.first_name or user.username, 'email': user.email, 'is_staff': user.is_staff or user.is_superuser})


@api_view(['POST'])
def password_reset_request(request):
    email = str(request.data.get('email') or '').strip()
    keys = [throttle_key('reset', 'ip', request.META.get('REMOTE_ADDR') or 'unknown')]
    if email:
        keys.append(throttle_key('reset', 'email', email))
    remaining = throttle_remaining(keys, 5)
    if remaining:
        response = Response({
            'error': f'Bạn đã yêu cầu quá nhiều liên kết. Vui lòng thử lại sau {remaining} giây.',
            'retry_after_seconds': remaining,
        }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        response['Retry-After'] = str(remaining)
        return response
    record_attempt(keys, 60 * 60)

    # Do not reveal whether an address belongs to an account.
    if email:
        users = User.objects.filter(email__iexact=email, is_active=True).order_by('date_joined', 'pk')
        user = users.first()
        if user:
            if users.count() > 1:
                logger.warning('Nhiều tài khoản đang hoạt động dùng email %s; chỉ gửi cho tài khoản %s.', email, user.pk)
            uid = urlsafe_base64_encode(str(user.pk).encode())
            token = default_token_generator.make_token(user)
            reset_url = f'{settings.FRONTEND_URL.rstrip("/")}/dat-lai-mat-khau?uid={uid}&token={token}'
            try:
                send_mail(
                    'Đặt lại mật khẩu tài khoản Đi Việt Nam',
                    f'Xin chào {user.username},\n\n'
                    f'Bạn có thể đặt lại mật khẩu tại liên kết sau:\n{reset_url}\n\n'
                    f'Liên kết có hiệu lực trong {settings.PASSWORD_RESET_TIMEOUT} giây kể từ khi được tạo.\n'
                    'Nếu không phải bạn yêu cầu thì bỏ qua email này.\n',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
            except Exception:
                logger.exception('Không gửi được email đặt lại mật khẩu cho tài khoản %s.', user.pk)
    return Response({'message': 'Nếu email tồn tại trong hệ thống, hướng dẫn đặt lại mật khẩu đã được gửi.'})


@api_view(['POST'])
def password_reset_confirm(request):
    uid = request.data.get('uid', '')
    token = request.data.get('token', '')
    password = request.data.get('password') or ''
    try:
        user = User.objects.get(pk=force_str(urlsafe_base64_decode(uid)))
    except (TypeError, ValueError, OverflowError, UnicodeDecodeError, User.DoesNotExist):
        return Response({'error': 'Liên kết đặt lại mật khẩu đã hết hạn hoặc đã được sử dụng.', 'code': 'invalid_or_expired_token'}, status=status.HTTP_400_BAD_REQUEST)
    if not default_token_generator.check_token(user, token):
        return Response({'error': 'Liên kết đặt lại mật khẩu đã hết hạn hoặc đã được sử dụng.', 'code': 'invalid_or_expired_token'}, status=status.HTTP_400_BAD_REQUEST)
    confirmation = request.data.get('password_confirm')
    if confirmation is not None and password != confirmation:
        return Response({'error': 'Hai mật khẩu chưa khớp.'}, status=status.HTTP_400_BAD_REQUEST)
    errors = password_errors(password, user)
    if errors:
        return Response({'error': ' '.join(errors), 'password_errors': errors}, status=status.HTTP_400_BAD_REQUEST)
    user.set_password(password)
    user.save(update_fields=['password'])
    return Response({'success': True, 'message': 'Mật khẩu đã được cập nhật. Vui lòng đăng nhập.'})


@api_view(['GET', 'PATCH'])
def profile_detail(request, user_id):
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return Response({'error': 'Không tìm thấy người dùng.'}, status=status.HTTP_404_NOT_FOUND)
    if not request.user.is_authenticated:
        return Response({'detail': 'Bạn không có quyền truy cập hồ sơ này.'}, status=status.HTTP_403_FORBIDDEN)
    is_owner = request.user.id == user_id
    if not is_owner and not (request.method == 'GET' and (request.user.is_staff or request.user.is_superuser)):
        return Response({'detail': 'Bạn không có quyền truy cập hồ sơ này.'}, status=status.HTTP_403_FORBIDDEN)

    profile = UserProfile.objects.filter(user=user).first()
    if profile is None:
        return Response({'error': 'Không tìm thấy hồ sơ người dùng.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'PATCH':
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            profile.refresh_from_db()
            return Response({
                'id': user.id,
                'username': user.username,
                'display_name': user.first_name or user.username,
                'email': user.email,
                'travel_preferences': profile.travel_preferences,
                'budget_estimate': str(profile.budget_estimate),
                'weather_preference': profile.weather_preference,
                'free_text': profile.free_text,
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        'id': user.id,
        'username': user.username,
        'display_name': user.first_name or user.username,
        'email': user.email,
        'travel_preferences': profile.travel_preferences,
        'budget_estimate': str(profile.budget_estimate),
        'weather_preference': profile.weather_preference,
        'free_text': profile.free_text,
    })


@api_view(['GET', 'POST'])
def search_history_view(request):
    if not request.user.is_authenticated:
        return Response({'detail': 'Vui lòng đăng nhập để xem lịch sử tìm kiếm.'}, status=status.HTTP_401_UNAUTHORIZED)

    if request.method == 'GET':
        queryset = SearchHistory.objects.select_related('user', 'destination').filter(user=request.user).order_by('-created_at')
        return Response(SearchHistorySerializer(queryset, many=True).data)

    payload = request.data.copy()
    serializer = SearchHistorySerializer(data=payload)
    if serializer.is_valid():
        history = serializer.save(user=request.user)
        return Response(SearchHistorySerializer(history).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
def chat_message_list(request):
    if not request.user.is_authenticated:
        return Response({'detail': 'Vui lòng đăng nhập để sử dụng trò chuyện.'}, status=status.HTTP_401_UNAUTHORIZED)
    conversation_user_id = request.query_params.get('conversation_user_id') or request.data.get('conversation_user_id') or request.query_params.get('user_id')
    try:
        conversation_user_id = int(conversation_user_id)
    except (TypeError, ValueError):
        return Response({'detail': 'Cuộc trò chuyện không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)
    if not (request.user.is_staff or request.user.is_superuser) and request.user.id != conversation_user_id:
        return Response({'detail': 'Bạn không có quyền xem cuộc trò chuyện này.'}, status=status.HTTP_403_FORBIDDEN)
    if not User.objects.filter(id=conversation_user_id).exists():
        return Response({'detail': 'Không tìm thấy người dùng.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        queryset = ChatMessage.objects.filter(conversation_user_id=conversation_user_id).select_related('sender').order_by('-created_at')
        page = Paginator(queryset, 50).get_page(request.query_params.get('page', 1))
        return Response({'results': ChatMessageSerializer(page.object_list[::-1], many=True, context={'request': request}).data,
                         'page': page.number, 'num_pages': page.paginator.num_pages, 'count': page.paginator.count})

    content = str(request.data.get('content', '')).strip()
    attachment_name = ''
    attachment_url = str(request.data.get('attachment_url', '')).strip()
    attachment_type = request.data.get('attachment_type', 'none')
    if attachment_url:
        path = urlparse(attachment_url).path
        prefix = settings.MEDIA_URL.rstrip('/') + '/'
        if not path.startswith(prefix):
            return Response({'detail': 'Tệp đính kèm không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)
        candidate = path[len(prefix):].lstrip('/')
        if '..' in PurePosixPath(candidate).parts or not candidate.startswith(f'chat_attachments/user_{conversation_user_id}/'):
            return Response({'detail': 'Đường dẫn tệp không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)
        extension = PurePosixPath(candidate).suffix.lower()
        if not ((attachment_type == 'image' and extension in {'.jpg', '.jpeg', '.png', '.webp'}) or (attachment_type == 'pdf' and extension == '.pdf')):
            return Response({'detail': 'Chỉ hỗ trợ ảnh và PDF.'}, status=status.HTTP_400_BAD_REQUEST)
        if not default_storage.exists(candidate) or default_storage.size(candidate) > 5 * 1024 * 1024:
            return Response({'detail': 'Tệp không tồn tại hoặc vượt quá 5 MB.'}, status=status.HTTP_400_BAD_REQUEST)
        attachment_name = candidate
    if not (content or attachment_name):
        return Response({'detail': 'Tin nhắn không được để trống.'}, status=status.HTTP_400_BAD_REQUEST)
    message = ChatMessage.objects.create(
        conversation_user_id=conversation_user_id, sender=request.user,
        is_from_admin=bool(request.user.is_staff or request.user.is_superuser),
        content=content, attachment=attachment_name,
        attachment_type=attachment_type if attachment_name else 'none',
    )
    return Response(ChatMessageSerializer(message, context={'request': request}).data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def chat_upload(request):
    if not request.user.is_authenticated:
        return Response({'detail': 'Vui lòng đăng nhập trước khi gửi tệp.'}, status=status.HTTP_401_UNAUTHORIZED)
    try:
        conversation_user_id = int(request.data.get('conversation_user_id'))
    except (TypeError, ValueError):
        return Response({'detail': 'Cuộc trò chuyện không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)
    if not (request.user.is_staff or request.user.is_superuser) and request.user.id != conversation_user_id:
        return Response({'detail': 'Bạn không có quyền gửi tệp vào cuộc trò chuyện này.'}, status=status.HTTP_403_FORBIDDEN)
    if not User.objects.filter(id=conversation_user_id).exists():
        return Response({'detail': 'Không tìm thấy người dùng.'}, status=status.HTTP_404_NOT_FOUND)
    uploaded_file = request.FILES.get('file')
    if not uploaded_file:
        return Response({'error': 'Vui lòng chọn tệp đính kèm.'}, status=status.HTTP_400_BAD_REQUEST)

    extension = os.path.splitext(uploaded_file.name)[1].lower()
    image_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
    pdf_extension = '.pdf'
    content_type = (uploaded_file.content_type or '').lower()
    if extension in image_extensions:
        attachment_type = 'image'
        max_size = 5 * 1024 * 1024
        if not content_type.startswith('image/'):
            return Response({'error': 'Tệp tải lên không phải là ảnh hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)
    elif extension == pdf_extension:
        attachment_type = 'pdf'
        max_size = 5 * 1024 * 1024
        if content_type != 'application/pdf':
            return Response({'error': 'Tệp tải lên không phải PDF hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({'error': 'Chỉ hỗ trợ JPG, JPEG, PNG, WEBP và PDF.'}, status=status.HTTP_400_BAD_REQUEST)
    if uploaded_file.size > max_size:
        return Response({'error': f'Tệp {attachment_type} vượt quá dung lượng cho phép.'}, status=status.HTTP_400_BAD_REQUEST)

    if '/' in uploaded_file.name or '\\' in uploaded_file.name or '..' in uploaded_file.name:
        return Response({'error': 'Tên tệp không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)
    safe_name = os.path.basename(uploaded_file.name)
    attachment_name = default_storage.save(f'chat_attachments/user_{conversation_user_id}/{date.today():%Y/%m}/{uuid.uuid4().hex}_{safe_name}', uploaded_file)
    attachment_url = default_storage.url(attachment_name)
    return Response({
        'attachment_url': request.build_absolute_uri(attachment_url),
        'attachment_type': attachment_type,
        'attachment_name': uploaded_file.name,
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def admin_chat_conversations(request):
    denied = require_admin(request)
    if denied:
        return denied
    user_ids = ChatMessage.objects.exclude(conversation_user__isnull=True).values_list('conversation_user_id', flat=True).distinct()
    conversations = []
    for chat_user in User.objects.filter(id__in=user_ids):
        messages = ChatMessage.objects.filter(conversation_user=chat_user).select_related('sender').order_by('-created_at')
        latest = messages.first()
        if not latest:
            continue
        conversations.append({
            'user': {'id': chat_user.id, 'username': chat_user.get_username()},
            'last_message': ChatMessageSerializer(latest, context={'request': request}).data,
            'last_message_at': latest.created_at.isoformat(),
            'unread_count': messages.filter(is_from_admin=False, is_read=False).count(),
        })
    conversations.sort(key=lambda item: item['last_message_at'], reverse=True)
    return Response({'results': conversations})


@api_view(['GET'])
def chat_unread_count(request):
    if not request.user.is_authenticated:
        return Response({'detail': 'Vui lòng đăng nhập.'}, status=status.HTTP_401_UNAUTHORIZED)
    messages = ChatMessage.objects.filter(is_read=False)
    if request.user.is_staff or request.user.is_superuser:
        count = messages.filter(is_from_admin=False).count()
    else:
        count = messages.filter(
            conversation_user_id=request.user.id, is_from_admin=True,
        ).count()
    return Response({'count': count})


@api_view(['POST'])
def chat_mark_read(request, user_id):
    if not request.user.is_authenticated:
        return Response({'detail': 'Vui lòng đăng nhập.'}, status=status.HTTP_401_UNAUTHORIZED)
    if not (request.user.is_staff or request.user.is_superuser) and request.user.id != user_id:
        return Response({'detail': 'Bạn không có quyền cập nhật cuộc trò chuyện này.'}, status=status.HTTP_403_FORBIDDEN)
    if not User.objects.filter(id=user_id).exists():
        return Response({'detail': 'Không tìm thấy người dùng.'}, status=status.HTTP_404_NOT_FOUND)
    unread = ChatMessage.objects.filter(conversation_user_id=user_id, is_read=False)
    if request.user.is_staff or request.user.is_superuser:
        unread = unread.filter(is_from_admin=False)
    else:
        unread = unread.filter(is_from_admin=True)
    unread.update(is_read=True)
    if request.user.is_staff or request.user.is_superuser:
        count = ChatMessage.objects.filter(is_from_admin=False, is_read=False).count()
        group_name = 'notify_admins'
    else:
        count = ChatMessage.objects.filter(
            conversation_user_id=request.user.id, is_from_admin=True, is_read=False,
        ).count()
        group_name = f'notify_user_{request.user.id}'
    channel_layer = get_channel_layer()
    if channel_layer:
        async_to_sync(channel_layer.group_send)(group_name, {
            'type': 'unread_event', 'count': count,
            'conversation_id': user_id, 'preview': '',
        })
    return Response({'status': 'ok', 'count': count})


@api_view(['GET', 'POST'])
def review_list_create(request):
    if request.method == 'GET':
        accommodation_id = request.GET.get('accommodation')
        queryset = AccommodationReview.objects.select_related('user', 'user__profile', 'accommodation').all().order_by('-created_at')
        if accommodation_id:
            queryset = queryset.filter(accommodation_id=accommodation_id)
        return Response(AccommodationReviewSerializer(queryset, many=True).data)

    if not request.user.is_authenticated:
        return Response({'detail': 'Vui lòng đăng nhập để gửi đánh giá.'}, status=status.HTTP_401_UNAUTHORIZED)
    booking_id = request.data.get('booking')
    try:
        booking = Booking.objects.select_related('room_type__accommodation').get(pk=booking_id)
    except (Booking.DoesNotExist, TypeError, ValueError):
        return Response({'detail': 'Không tìm thấy đơn đặt phòng.'}, status=status.HTTP_404_NOT_FOUND)
    if booking.user_id != request.user.id:
        return Response({'detail': 'Bạn không có quyền đánh giá đơn này.'}, status=status.HTTP_403_FORBIDDEN)
    if booking.status != 'confirmed' or booking.check_out >= timezone.localdate():
        return Response(
            {'detail': 'Chỉ có thể đánh giá sau khi đơn đã xác nhận và ngày trả phòng đã qua.'},
            status=status.HTTP_403_FORBIDDEN,
        )
    if AccommodationReview.objects.filter(booking=booking).exists():
        return Response(
            {'detail': 'Đơn đặt phòng này đã được đánh giá.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = AccommodationReviewSerializer(data=request.data)
    if serializer.is_valid():
        review = serializer.save(
            booking=booking,
            user=request.user,
            accommodation=booking.room_type.accommodation,
        )
        average = AccommodationReview.objects.filter(
            accommodation=review.accommodation,
        ).aggregate(value=Avg('rating'))['value'] or 0
        Accommodation.objects.filter(pk=review.accommodation_id).update(rating=average)
        return Response(AccommodationReviewSerializer(review).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------------------------
# TravelPost
# ---------------------------------------------------------------------------

_TRAVEL_POST_PAGE_SIZE = 10


@api_view(['GET', 'POST'])
def travel_post_list_create(request):
    """GET /api/travel-posts/ - danh sach; POST - tao moi (phai dang nhap)."""
    if request.method == 'GET':
        qs = TravelPost.objects.select_related('user', 'user__profile', 'destination').order_by('-created_at')

        destination_id = request.query_params.get('destination_id')
        if destination_id:
            qs = qs.filter(destination_id=destination_id)

        sort = request.query_params.get('sort', '-created_at')
        allowed_sorts = ['-created_at', 'created_at', '-likes_count', 'likes_count']
        if sort in allowed_sorts:
            qs = qs.order_by(sort)

        try:
            page = max(1, int(request.query_params.get('page', 1)))
        except ValueError:
            page = 1

        total = qs.count()
        start = (page - 1) * _TRAVEL_POST_PAGE_SIZE
        posts = qs[start: start + _TRAVEL_POST_PAGE_SIZE]

        serializer = TravelPostSerializer(posts, many=True, context={'request': request})
        return Response({
            'count': total,
            'page': page,
            'page_size': _TRAVEL_POST_PAGE_SIZE,
            'total_pages': max(1, math.ceil(total / _TRAVEL_POST_PAGE_SIZE)),
            'results': serializer.data,
        })

    if not request.user.is_authenticated:
        return Response({'detail': 'Vui lòng đăng nhập để đăng bài.'}, status=status.HTTP_401_UNAUTHORIZED)

    serializer = TravelPostSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        post = serializer.save(user=request.user)
        return Response(TravelPostSerializer(post, context={'request': request}).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'DELETE'])
def travel_post_detail(request, post_id):
    """GET /api/travel-posts/<id>/ - chi tiet; DELETE - xoa (chu bai hoac admin)."""
    post = get_object_or_404(TravelPost, pk=post_id)

    if request.method == 'GET':
        serializer = TravelPostSerializer(post, context={'request': request})
        return Response(serializer.data)

    if not request.user.is_authenticated:
        return Response({'detail': 'Vui lòng đăng nhập để tiếp tục.'}, status=status.HTTP_401_UNAUTHORIZED)
    if post.user != request.user and not (request.user.is_staff or request.user.is_superuser):
        return Response({'detail': 'Bạn không có quyền xóa bài viết này.'}, status=status.HTTP_403_FORBIDDEN)

    post.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
def travel_post_like(request, post_id):
    """POST /api/travel-posts/<id>/like/ - toggle like/unlike."""
    if not request.user.is_authenticated:
        return Response({'detail': 'Vui lòng đăng nhập để thích bài viết.'}, status=status.HTTP_401_UNAUTHORIZED)

    post = get_object_or_404(TravelPost, pk=post_id)

    like, created = TravelPostLike.objects.get_or_create(user=request.user, post=post)
    if created:
        TravelPost.objects.filter(pk=post_id).update(likes_count=post.likes_count + 1)
        post.refresh_from_db(fields=['likes_count'])
        is_liked = True
    else:
        like.delete()
        TravelPost.objects.filter(pk=post_id).update(likes_count=max(0, post.likes_count - 1))
        post.refresh_from_db(fields=['likes_count'])
        is_liked = False

    return Response({'likes_count': post.likes_count, 'is_liked': is_liked})
