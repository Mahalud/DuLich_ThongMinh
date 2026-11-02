from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import Accommodation, Destination, RoomType, Tour, TourStop


class Command(BaseCommand):
    help = 'Seed real Vietnamese destination data and demo accommodation inventory.'

    def handle(self, *args, **options):
        destinations = [
            {
                'name': 'Phú Quốc',
                'description': 'Đảo Phú Quốc là điểm du lịch biển nổi tiếng với bãi biển dài, nước trong và hoạt động lặn biển, nghỉ dưỡng, thưởng thức hải sản.',
                'category': 'biển',
                'latitude': 10.2233,
                'longitude': 103.9607,
                'image_url': 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80',
                'rating': 4.8,
            },
            {
                'name': 'Hội An',
                'description': 'Thành phố cổ Hội An nổi tiếng với kiến trúc cổ, đèn lồng, phố đi bộ, ẩm thực và bãi biển gần đó.',
                'category': 'thành phố',
                'latitude': 15.8801,
                'longitude': 108.3380,
                'image_url': 'https://images.unsplash.com/photo-1528127269322-539801943592?auto=format&fit=crop&w=1200&q=80',
                'rating': 4.7,
            },
            {
                'name': 'Đà Lạt',
                'description': 'Đà Lạt là thành phố ngàn hoa, mát mẻ quanh năm với vườn hoa, hồ, đồi thông và không khí mát.',
                'category': 'núi',
                'latitude': 11.9404,
                'longitude': 108.4583,
                'image_url': 'https://images.unsplash.com/photo-1501785888041-af3ef285b470?auto=format&fit=crop&w=1200&q=80',
                'rating': 4.6,
            },
            {
                'name': 'Nha Trang',
                'description': 'Nha Trang là trung tâm du lịch biển miền Trung với bãi cát đẹp, đảo và các hoạt động lặn, câu cá.',
                'category': 'biển',
                'latitude': 12.2388,
                'longitude': 109.1967,
                'image_url': 'https://images.unsplash.com/photo-1500375592092-40eb2168fd21?auto=format&fit=crop&w=1200&q=80',
                'rating': 4.7,
            },
            {
                'name': 'Sa Pa',
                'description': 'Sa Pa là trung tâm du lịch núi cao với ruộng bậc thang, bản làng dân tộc và khí hậu mát quanh năm.',
                'category': 'núi',
                'latitude': 22.3360,
                'longitude': 103.8438,
                'image_url': 'https://images.unsplash.com/photo-1516483638261-f4dbaf036963?auto=format&fit=crop&w=1200&q=80',
                'rating': 4.6,
            },
            {
                'name': 'Vũng Tàu',
                'description': 'Vũng Tàu nổi tiếng với bãi biển, du lịch nghỉ dưỡng, ăn hải sản và cảnh quan biển dễ tiếp cận từ TP.HCM.',
                'category': 'biển',
                'latitude': 10.3460,
                'longitude': 107.0841,
                'image_url': 'https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=80',
                'rating': 4.4,
            },
            {
                'name': 'Hà Giang',
                'description': 'Hà Giang là vùng cao nguyên đá phía Bắc với đường đèo, làng sắc màu và trải nghiệm du lịch mạo hiểm.',
                'category': 'núi',
                'latitude': 22.8026,
                'longitude': 104.9830,
                'image_url': 'https://images.unsplash.com/photo-1501555088652-021fa9c939b0?auto=format&fit=crop&w=1200&q=80',
                'rating': 4.8,
            },
        ]

        for payload in destinations:
            Destination.objects.update_or_create(
                name=payload['name'],
                defaults={
                    'description': payload['description'],
                    'category': payload['category'],
                    'latitude': payload['latitude'],
                    'longitude': payload['longitude'],
                    'image_url': payload['image_url'],
                    'rating': payload['rating'],
                },
            )

        tour_data = [
            ('Tour 3N2Đ: Đà Lạt - Nha Trang', 'Hành trình cao nguyên và biển.', 3, 4290000, ['Đà Lạt', 'Nha Trang']),
            ('Tour 4N3Đ: Hội An - Phú Quốc', 'Phố cổ, biển xanh và ẩm thực.', 4, 5990000, ['Hội An', 'Phú Quốc']),
        ]
        for name, description, duration, price, stops in tour_data:
            tour, _ = Tour.objects.update_or_create(name=name, defaults={'description': description, 'duration_days': duration, 'price_per_person': price, 'cover_image_url': 'https://images.unsplash.com/photo-1488646953014-85cb44e25828?auto=format&fit=crop&w=1200&q=80', 'is_active': True})
            TourStop.objects.filter(tour=tour).delete()
            for day, destination_name in enumerate(stops, 1):
                TourStop.objects.create(tour=tour, destination=Destination.objects.get(name=destination_name), day_number=day, note=f'Tham quan {destination_name}.')

        accommodation_data = [
            {
                'name': 'Azure Bay Lodge',
                'destination': 'Phú Quốc',
                'description': 'Demo chỗ ở ven biển, phục vụ du lịch nghỉ dưỡng, khoảng cách ngắn đến bãi biển và các địa điểm ăn uống.',
                'category': 'hotel',
                'latitude': 10.2300,
                'longitude': 103.9680,
                'rating': 4.8,
                'room_types': [
                    {'name': 'Phòng đơn', 'base_price': 1200000, 'stock': 5, 'amenities': ['wifi', 'dieu_hoa', 'giat_ui', 'bon_tam']},
                    {'name': 'Phòng đôi', 'base_price': 1800000, 'stock': 4, 'amenities': ['wifi', 'dieu_hoa', 'ban_cong', 'huong_bien']},
                    {'name': 'Phòng gia đình', 'base_price': 2600000, 'stock': 3, 'amenities': ['wifi', 'dieu_hoa', 'bep', 'ho_boi']},
                ],
            },
            {
                'name': 'Lantern Courtyard Stay',
                'destination': 'Hội An',
                'description': 'Demo homestay ở Hội An với phong cách cổ điển, gần phố cổ và các điểm check-in đẹp.',
                'category': 'homestay',
                'latitude': 15.8740,
                'longitude': 108.3450,
                'rating': 4.7,
                'room_types': [
                    {'name': 'Phòng đơn', 'base_price': 900000, 'stock': 6, 'amenities': ['wifi', 'dieu_hoa', 'bon_tam', 'ban_cong']},
                    {'name': 'Phòng đôi', 'base_price': 1400000, 'stock': 5, 'amenities': ['wifi', 'dieu_hoa', 'tivi', 'thang_may']},
                    {'name': 'Phòng gia đình', 'base_price': 2200000, 'stock': 2, 'amenities': ['wifi', 'dieu_hoa', 'bep', 'bua_sang']},
                ],
            },
            {
                'name': 'Cloud Valley Retreat',
                'destination': 'Đà Lạt',
                'description': 'Demo chỗ ở ở Đà Lạt với không khí mát mẻ, nhìn ra đồi thông và khu vườn hoa.',
                'category': 'hotel',
                'latitude': 11.9480,
                'longitude': 108.4650,
                'rating': 4.6,
                'room_types': [
                    {'name': 'Phòng đơn', 'base_price': 1000000, 'stock': 5, 'amenities': ['wifi', 'dieu_hoa', 'bon_tam', 'bua_sang']},
                    {'name': 'Phòng đôi', 'base_price': 1600000, 'stock': 4, 'amenities': ['wifi', 'dieu_hoa', 'bep', 'ban_cong']},
                    {'name': 'Phòng gia đình', 'base_price': 2400000, 'stock': 3, 'amenities': ['wifi', 'dieu_hoa', 'ho_boi', 'do_xe']},
                ],
            },
            {
                'name': 'Nha Trang Seaside Stay',
                'destination': 'Nha Trang',
                'description': 'Demo chỗ ở ven biển Nha Trang, thuận tiện đi bộ tới bãi biển và các điểm ăn uống trung tâm.',
                'category': 'hotel',
                'latitude': 12.2450,
                'longitude': 109.1950,
                'rating': 4.5,
                'room_types': [
                    {'name': 'Phòng đôi', 'base_price': 1500000, 'stock': 4, 'amenities': ['wifi', 'dieu_hoa', 'ban_cong']},
                ],
            },
        ]

        for payload in accommodation_data:
            accommodation, _ = Accommodation.objects.update_or_create(
                name=payload['name'],
                defaults={
                    'destination': Destination.objects.get(name=payload['destination']),
                    'description': payload['description'],
                    'category': payload['category'],
                    'latitude': payload['latitude'],
                    'longitude': payload['longitude'],
                    'rating': payload['rating'],
                },
            )

            for room in payload['room_types']:
                RoomType.objects.update_or_create(
                    accommodation=accommodation,
                    name=room['name'],
                    defaults={
                        'base_price': room['base_price'],
                        'stock': room['stock'],
                        'amenities': room['amenities'],
                    },
                )

        self.stdout.write(self.style.SUCCESS('Đã seed dữ liệu điểm đến thực và chỗ ở demo thành công.'))
