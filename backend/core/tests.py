import os

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import Accommodation, Booking, Destination, RoomType, UserProfile

User = get_user_model()


class BookingLogicTests(TestCase):
    def setUp(self):
        os.environ['FERNET_KEY'] = 'z9KtdV-hxepGPhW3oGdOfj_mOuAGEJQ7gDT9cMGx7d0='
        self.user = User.objects.create_user(username='traveler', email='traveler@example.com', password='secret123')
        self.user_profile = UserProfile.objects.create(
            user=self.user,
            travel_preferences=['biển', 'ẩm thực'],
            budget_estimate=5000000,
            free_text='Muốn nghỉ dưỡng và ăn ngon',
        )

        self.destination = Destination.objects.create(
            name='Nha Trang',
            description='Bãi biển đẹp',
            category='biển',
            latitude=12.2500,
            longitude=109.1900,
            rating=4.6,
        )

        self.accommodation = Accommodation.objects.create(
            name='Seashell Stay',
            description='Homestay gần biển',
            category='homestay',
            latitude=12.2500,
            longitude=109.1900,
            rating=4.5,
        )

        self.room_type = RoomType.objects.create(
            accommodation=self.accommodation,
            name='Phòng đôi',
            base_price=1500000,
            stock=1,
        )

    def test_phone_is_encrypted_before_save(self):
        booking = Booking.objects.create(
            user=self.user,
            room_type=self.room_type,
            check_in='2026-09-10',
            check_out='2026-09-12',
            guest_phone='0909999999',
        )

        self.assertNotEqual(booking.guest_phone, '0909999999')
        self.assertNotEqual(booking.decrypt_guest_phone(), booking.guest_phone)
        self.assertEqual(booking.decrypt_guest_phone(), '0909999999')

    def test_booking_overlap_validation_rejects_exceeding_stock(self):
        Booking.objects.create(
            user=self.user,
            room_type=self.room_type,
            check_in='2026-09-10',
            check_out='2026-09-12',
            guest_phone='0911111111',
        )

        second_booking = Booking(
            user=self.user,
            room_type=self.room_type,
            check_in='2026-09-11',
            check_out='2026-09-13',
            guest_phone='0922222222',
        )

        with self.assertRaises(ValidationError):
            second_booking.clean()

    def test_recommendations_endpoint_returns_ranked_destinations(self):
        client = APIClient()
        response = client.get('/api/recommendations/', {
            'user_preferences': 'biển,ẩm thực',
            'budget_estimate': 5000000,
            'latitude': 12.25,
            'longitude': 109.19,
            'travel_date': '2026-09-12',
            'top_n': 3,
        })

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('results', data)
        self.assertTrue(len(data['results']) >= 1)
        self.assertIn('score', data['results'][0])

    def test_recommendation_explanation_endpoint_returns_personalized_summary(self):
        client = APIClient()
        response = client.get('/api/recommendations/explain/', {
            'user_preferences': 'biển,ẩm thực',
            'budget_estimate': 5000000,
            'latitude': 12.25,
            'longitude': 109.19,
            'travel_date': '2026-09-12',
            'top_n': 3,
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn('explanation', response.json())
        self.assertIn('top_destination', response.json())

    def test_accommodation_api_lists_rooms(self):
        client = APIClient()
        response = client.get('/api/accommodations/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(isinstance(response.json(), list))

    def test_booking_api_rejects_overlapping_dates_when_stock_is_full(self):
        client = APIClient()
        Booking.objects.create(
            user=self.user,
            room_type=self.room_type,
            check_in='2026-09-10',
            check_out='2026-09-12',
            guest_phone='0911111111',
        )

        response = client.post('/api/bookings/', {
            'user': self.user.id,
            'room_type': self.room_type.id,
            'check_in': '2026-09-11',
            'check_out': '2026-09-13',
            'guest_phone': '0922222222',
        }, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertIn('Không còn phòng', str(response.data))

    def test_weather_api_returns_forecast_summary(self):
        client = APIClient()
        response = client.get('/api/weather/', {
            'latitude': '12.25',
            'longitude': '109.19',
            'date': '2026-09-12',
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn('temperature', response.json())
        self.assertIn('weather_score', response.json())

    def test_auth_register_and_profile_endpoints(self):
        client = APIClient()
        register_response = client.post('/api/auth/register/', {
            'username': 'newtraveler',
            'email': 'newtraveler@example.com',
            'password': 'StrongPass123',
        }, format='json')

        self.assertEqual(register_response.status_code, 201)
        self.assertEqual(register_response.json()['username'], 'newtraveler')

        login_response = client.post('/api/auth/login/', {
            'username': 'newtraveler',
            'password': 'StrongPass123',
        }, format='json')

        self.assertEqual(login_response.status_code, 200)
        self.assertTrue(login_response.json()['success'])

        profile_response = client.get(f'/api/profile/{register_response.json()["id"]}/')
        self.assertEqual(profile_response.status_code, 200)
        self.assertEqual(profile_response.json()['username'], 'newtraveler')

    def test_admin_destination_crud_flow(self):
        client = APIClient()
        create_response = client.post('/api/admin/destinations/', {
            'name': 'Phú Quốc',
            'description': 'Đảo biển đẹp',
            'category': 'biển',
            'latitude': 10.25,
            'longitude': 103.97,
            'image_url': 'https://example.com/phuquoc.jpg',
            'rating': 4.9,
        }, format='json')

        self.assertEqual(create_response.status_code, 201)
        destination_id = create_response.json()['id']

        list_response = client.get('/api/admin/destinations/')
        self.assertEqual(list_response.status_code, 200)
        self.assertTrue(any(item['id'] == destination_id for item in list_response.json()))

        patch_response = client.patch(f'/api/admin/destinations/{destination_id}/', {
            'name': 'Phú Quốc cập nhật',
        }, format='json')
        self.assertEqual(patch_response.status_code, 200)
        self.assertEqual(patch_response.json()['name'], 'Phú Quốc cập nhật')

    def test_admin_accommodation_crud_flow(self):
        client = APIClient()
        create_response = client.post('/api/admin/accommodations/', {
            'name': 'Azure Beach Lodge',
            'description': 'Chỗ ở gần biển',
            'category': 'hotel',
            'latitude': 12.3,
            'longitude': 109.2,
            'rating': 4.6,
        }, format='json')

        self.assertEqual(create_response.status_code, 201)
        accommodation_id = create_response.json()['id']

        list_response = client.get('/api/admin/accommodations/')
        self.assertEqual(list_response.status_code, 200)
        self.assertTrue(any(item['id'] == accommodation_id for item in list_response.json()))

        delete_response = client.delete(f'/api/admin/accommodations/{accommodation_id}/')
        self.assertEqual(delete_response.status_code, 204)

    def test_seed_real_travel_data_command_creates_real_destinations(self):
        call_command('seed_real_travel_data')

        self.assertTrue(Destination.objects.filter(name='Phú Quốc').exists())
        self.assertTrue(Destination.objects.filter(name='Hội An').exists())
        self.assertTrue(Destination.objects.filter(name='Đà Lạt').exists())
        self.assertTrue(Accommodation.objects.filter(name='Azure Bay Lodge').exists())
        self.assertTrue(RoomType.objects.filter(name='Phòng đôi').exists())

    def test_admin_room_type_crud_flow(self):
        accommodation = Accommodation.objects.create(
            name='Sunrise Garden',
            description='Demo chỗ ở',
            category='hotel',
            latitude=12.2,
            longitude=109.2,
            rating=4.7,
        )

        client = APIClient()
        create_response = client.post(f'/api/admin/accommodations/{accommodation.id}/room-types/', {
            'name': 'Phòng gia đình',
            'base_price': 2400000,
            'stock': 3,
            'amenities': ['wifi', 'điều hòa'],
        }, format='json')

        self.assertEqual(create_response.status_code, 201)
        room_type_id = create_response.json()['id']

        list_response = client.get(f'/api/admin/accommodations/{accommodation.id}/room-types/')
        self.assertEqual(list_response.status_code, 200)
        self.assertTrue(any(item['id'] == room_type_id for item in list_response.json()))

        patch_response = client.patch(f'/api/admin/room-types/{room_type_id}/', {
            'base_price': 2600000,
        }, format='json')
        self.assertEqual(patch_response.status_code, 200)
        self.assertEqual(patch_response.json()['base_price'], 2600000)

    def test_payment_init_and_return_flow(self):
        client = APIClient()
        booking = Booking.objects.create(
            user=self.user,
            room_type=self.room_type,
            check_in='2026-09-15',
            check_out='2026-09-18',
            guest_phone='0901234567',
        )

        init_response = client.post('/api/payments/init/', {
            'booking_id': booking.id,
            'amount': 1500000,
            'return_url': 'http://localhost:5173/payment-return',
        }, format='json')

        self.assertEqual(init_response.status_code, 200)
        self.assertIn('redirect_url', init_response.json())

        return_response = client.get('/api/payments/return/', {
            'booking_id': booking.id,
            'status': 'success',
        })

        self.assertEqual(return_response.status_code, 200)
        self.assertTrue(return_response.json()['success'])

        booking.refresh_from_db()
        self.assertEqual(booking.status, 'confirmed')

    def test_route_planning_returns_distance_duration_and_maps_link(self):
        client = APIClient()
        response = client.get('/api/routes/', {
            'start_lat': 12.25,
            'start_lng': 109.19,
            'end_lat': 12.30,
            'end_lng': 109.20,
        })

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn('distance_km', body)
        self.assertIn('duration_minutes', body)
        self.assertIn('google_maps_url', body)
