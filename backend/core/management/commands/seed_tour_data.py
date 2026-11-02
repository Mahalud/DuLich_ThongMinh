from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Destination, Tour, TourDeparture, TourStop


class Command(BaseCommand):
    help = 'Seed 3 sample tours with diverse categories, stops, and upcoming departures.'

    def handle(self, *args, **options):
        today = timezone.localdate()

        destinations = {d.name: d for d in Destination.objects.all()}

        tour_data = [
            {
                'name': 'Khám phá Vịnh Biển Nha Trang - Phú Quốc',
                'description': 'Hành trình khám phá thiên nhiên biển đảo tuyệt đẹp tại hai thiên đường nghỉ dưỡng hàng đầu Việt Nam. Quý khách được hòa mình vào làn nước ngọc bích, trải nghiệm lặn biển san hô và thưởng thức hải sản thượng hạng.',
                'category': 'kham_pha',
                'duration_days': 3,
                'price_adult': 3200000,
                'price_child': 2000000,
                'single_room_supplement': 500000,
                'min_age': 6,
                'included_services': [
                    'Xe du lịch máy lạnh đưa đón tham quan',
                    'Khách sạn 4 sao tiêu chuẩn 2 khách/phòng',
                    'Các bữa ăn đặc sản theo chương trình',
                    'Vé tham quan và tàu cano biển đảo',
                    'Bảo hiểm du lịch 50.000.000đ/vụ',
                    'Hướng dẫn viên nhiệt tình suốt tuyến',
                ],
                'excluded_services': [
                    'Chi phí cá nhân ngoài chương trình',
                    'Đồ uống có cồn trong các bữa ăn',
                    'Tiền tip cho tài xế và hướng dẫn viên',
                ],
                'cancellation_policy': 'Hủy trước 10 ngày khởi hành: Miễn phí 100%. Hủy từ 5 - 9 ngày: Phí 50%. Hủy dưới 5 ngày: Phí 100% tiền tour.',
                'cover_image_url': 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80',
                'stops': [
                    ('Nha Trang', 1, 'Đón khách tại sân bay Cam Ranh, tham quan Tháp Trầm Hương và ngắm hoàng hôn vịnh Nha Trang.'),
                    ('Nha Trang', 2, 'Cano cao tốc tham quan Hòn Mun, lặn biển ngắm san hô tự nhiên và ăn trưa bè nổi.'),
                    ('Phú Quốc', 3, 'Khám phá đảo ngọc Phú Quốc, cáp treo Hòn Thơm và mua sắm ngọc trai đảo ngọc.'),
                ],
                'departures': [
                    (today + timedelta(days=32), 15),
                    (today + timedelta(days=45), 15),
                    (today + timedelta(days=58), 15),
                ],
            },
            {
                'name': 'Hành trình Di sản Văn hóa Miền Trung: Hội An Cổ Kính',
                'description': 'Tour văn hóa - lịch sử đưa du khách về với không gian rêu phong cổ kính của Đô thị cổ Hội An. Chiêm ngưỡng kiến trúc giao thoa Đông - Tây, trải nghiệm nghề thủ công truyền thống và thả đèn hoa đăng lung linh.',
                'category': 'van_hoa',
                'duration_days': 4,
                'price_adult': 4500000,
                'price_child': 2800000,
                'single_room_supplement': 800000,
                'min_age': 5,
                'included_services': [
                    'Xe đưa đón chất lượng cao suốt tuyến',
                    'Khách sạn boutique phong cách cổ điển tại Hội An',
                    'Tất cả các vé tham quan di tích theo lịch trình',
                    'Thực đơn ẩm thực cung đình và đặc sản địa phương',
                    'Hướng dẫn viên chuyên gia văn hóa lịch sử',
                ],
                'excluded_services': [
                    'Thuế VAT 8%',
                    'Phụ thu phòng đơn nếu yêu cầu ở riêng',
                    'Dịch vụ giặt ủi, minibar tại khách sạn',
                ],
                'cancellation_policy': 'Hủy trước 14 ngày: Phí 10%. Hủy trước 7 ngày: Phí 40%. Hủy trước 3 ngày: Phí 80%. Hủy trong vòng 3 ngày: Không hoàn phí.',
                'cover_image_url': 'https://images.unsplash.com/photo-1528127269322-539801943592?auto=format&fit=crop&w=1200&q=80',
                'stops': [
                    ('Hội An', 1, 'Dạo bước phố cổ Hội An, tham quan Chùa Cầu Nhật Bản và hội quán Phúc Kiến.'),
                    ('Hội An', 2, 'Trải nghiệm chèo thuyền thúng rừng dừa Bảy Mẫu, học làm gốm Thanh Hà.'),
                    ('Nha Trang', 3, 'Di chuyển dọc cung đường duyên hải miền Trung, ghé thăm Viện Hải dương học.'),
                    ('Nha Trang', 4, 'Thư giãn tắm bùn khoáng Tháp Bà Ponagar, mua sắm đặc sản yến sào.'),
                ],
                'departures': [
                    (today + timedelta(days=35), 20),
                    (today + timedelta(days=48), 20),
                    (today + timedelta(days=60), 20),
                ],
            },
            {
                'name': 'Nghỉ dưỡng & Khí hậu Đà Lạt - Sa Pa sương mờ',
                'description': 'Kỳ nghỉ thư thái giữa không gian đồi thông và mây ngàn trong lành. Tránh xa ồn ào phố thị, thưởng thức hương vị cà phê Arabica cao nguyên thơm lừng và check-in các điểm đến thơ mộng bậc nhất.',
                'category': 'nghi_duong',
                'duration_days': 3,
                'price_adult': 2800000,
                'price_child': 1500000,
                'single_room_supplement': 400000,
                'min_age': 4,
                'included_services': [
                    'Resort nghỉ dưỡng cao cấp view thung lũng',
                    'Bữa sáng buffet thượng hạng mỗi ngày',
                    'Xe limousine đưa đón sân bay và các điểm tham quan',
                    'Vé tham quan trọn gói các điểm theo lịch trình',
                    'Nước uống và khăn lạnh hàng ngày',
                ],
                'excluded_services': [
                    'Vé cáp treo và máng trượt tự chọn',
                    'Các bữa ăn tối tự do khám phá chợ đêm',
                    'Chi phí phát sinh cá nhân',
                ],
                'cancellation_policy': 'Hủy trước 7 ngày: Hoàn tiền 100%. Hủy từ 3 đến 6 ngày: Hoàn 50%. Hủy trong vòng 48 giờ: Phạt 100% giá trị tour.',
                'cover_image_url': 'https://images.unsplash.com/photo-1501785888041-af3ef285b470?auto=format&fit=crop&w=1200&q=80',
                'stops': [
                    ('Đà Lạt', 1, 'Check-in đồi chè Cầu Đất săn mây, viếng chùa Linh Phước (Chùa Ve Chai).'),
                    ('Đà Lạt', 2, 'Khám phá thung lũng Tình Yêu, trải nghiệm máng trượt thác Datanla kì thú.'),
                    ('Sa Pa', 3, 'Dạo bước bản Cát Cát, chiêm ngưỡng ruộng bậc thang và chinh phục đỉnh Fansipan.'),
                ],
                'departures': [
                    (today + timedelta(days=30), 10),
                    (today + timedelta(days=42), 10),
                    (today + timedelta(days=55), 10),
                ],
            },
        ]

        for item in tour_data:
            tour, created = Tour.objects.update_or_create(
                name=item['name'],
                defaults={
                    'description': item['description'],
                    'category': item['category'],
                    'duration_days': item['duration_days'],
                    'price_adult': item['price_adult'],
                    'price_child': item['price_child'],
                    'single_room_supplement': item['single_room_supplement'],
                    'min_age': item['min_age'],
                    'included_services': item['included_services'],
                    'excluded_services': item['excluded_services'],
                    'cancellation_policy': item['cancellation_policy'],
                    'cover_image_url': item['cover_image_url'],
                    'is_active': True,
                },
            )

            # Xóa stops cũ và cập nhật lại
            tour.stops.all().delete()
            for dest_name, day_num, note in item['stops']:
                dest = destinations.get(dest_name)
                if dest:
                    TourStop.objects.create(
                        tour=tour,
                        destination=dest,
                        day_number=day_num,
                        note=note,
                    )

            # Cập nhật departures
            for dep_date, slots in item['departures']:
                TourDeparture.objects.update_or_create(
                    tour=tour,
                    departure_date=dep_date,
                    defaults={
                        'slots_total': slots,
                        'is_cancelled': False,
                    },
                )

            action_str = 'Tạo mới' if created else 'Cập nhật'
            self.stdout.write(self.style.SUCCESS(f'{action_str} tour: {tour.name}'))

        self.stdout.write(self.style.SUCCESS('Hoàn tất seed 3 tour mẫu đa dạng category và các chuyến khởi hành demo!'))
