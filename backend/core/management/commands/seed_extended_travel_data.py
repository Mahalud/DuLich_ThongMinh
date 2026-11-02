import math
import random
import logging
import time
import unicodedata
from datetime import date, timedelta

import requests
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from core.models import Amenity, Accommodation, Destination, RoomType, Tour, TourDeparture, TourStop


logger = logging.getLogger(__name__)


DESTINATIONS = [
    # North
    ('Sa Pa', 'Sa Pa, Việt Nam', 'núi', 'Thị trấn vùng cao nổi tiếng với ruộng bậc thang, bản làng người H’Mông và cung đường chinh phục Fansipan.'),
    ('Hà Giang', 'Hà Giang, Việt Nam', 'núi', 'Cao nguyên đá Đồng Văn, đèo Mã Pì Lèng và những cung đường khám phá miền biên viễn.'),
    ('Ninh Bình', 'Ninh Bình, Việt Nam', 'thành phố', 'Quần thể Tràng An, Tam Cốc và cố đô Hoa Lư với cảnh quan núi đá vôi và di tích lịch sử.'),
    ('Hạ Long', 'Vịnh Hạ Long, Việt Nam', 'biển', 'Di sản thiên nhiên thế giới với hàng nghìn đảo đá vôi và các tuyến tham quan vịnh.'),
    ('Cát Bà', 'Cát Bà', 'biển', 'Quần đảo Cát Bà, vịnh Lan Hạ và Vườn quốc gia Cát Bà với hoạt động chèo kayak, trekking.'),
    ('Mộc Châu', 'Mộc Châu, Sơn La, Việt Nam', 'núi', 'Cao nguyên chè, thác Dải Yếm và mùa hoa mận đặc trưng vùng Tây Bắc.'),
    ('Hà Nội', 'Hà Nội, Việt Nam', 'ẩm thực', 'Thủ đô với phố cổ, hồ Hoàn Kiếm, di tích lịch sử và văn hóa ẩm thực đường phố.'),
    ('Tam Đảo', 'Tam Đảo, Vĩnh Phúc, Việt Nam', 'núi', 'Thị trấn nghỉ mát trên núi với khí hậu mát, nhà thờ đá và các cung đường rừng.'),
    ('Ba Vì', 'Vườn quốc gia Ba Vì, Việt Nam', 'núi', 'Vườn quốc gia Ba Vì với rừng tự nhiên, nhà thờ cổ và các tuyến đi bộ lên núi.'),
    ('Thác Bản Giốc (Cao Bằng)', 'Thác Bản Giốc, Cao Bằng, Việt Nam', 'núi', 'Thác Bản Giốc trên sông Quây Sơn, một trong những thác nước tự nhiên nổi tiếng nhất Việt Nam.'),
    ('Mai Châu', 'Mai Châu, Hòa Bình, Việt Nam', 'núi', 'Thung lũng Mai Châu với bản làng người Thái, nhà sàn và đường đạp xe qua cánh đồng.'),
    ('Pù Luông', 'Khu bảo tồn thiên nhiên Pù Luông, Việt Nam', 'núi', 'Khu bảo tồn Pù Luông với ruộng bậc thang, bản làng và các tuyến trekking.'),
    # Central
    ('Huế', 'Huế, Việt Nam', 'thành phố', 'Cố đô Huế với Đại Nội, lăng tẩm triều Nguyễn, chùa Thiên Mụ và ẩm thực cung đình.'),
    ('Đà Nẵng', 'Đà Nẵng, Việt Nam', 'biển', 'Thành phố biển với bán đảo Sơn Trà, Ngũ Hành Sơn, bãi biển Mỹ Khê và cầu Rồng.'),
    ('Hội An', 'Phố cổ Hội An, Việt Nam', 'thành phố', 'Đô thị cổ được UNESCO ghi danh, nổi bật với kiến trúc phố cổ, đèn lồng và ẩm thực địa phương.'),
    ('Phong Nha - Kẻ Bàng', 'Vườn quốc gia Phong Nha - Kẻ Bàng, Việt Nam', 'núi', 'Di sản thiên nhiên thế giới với hệ thống hang động, sông ngầm và tuyến khám phá mạo hiểm.'),
    ('Quy Nhơn', 'Quy Nhơn, Bình Định, Việt Nam', 'biển', 'Thành phố biển với Eo Gió, Kỳ Co, Ghềnh Ráng và các di tích văn hóa Chăm.'),
    ('Phú Yên', 'Phú Yên, Việt Nam', 'biển', 'Gành Đá Đĩa, Bãi Xép và đường bờ biển đặc trưng miền duyên hải Nam Trung Bộ.'),
    ('Nha Trang', 'Nha Trang, Việt Nam', 'biển', 'Vịnh Nha Trang, bãi biển Trần Phú, các đảo ven bờ và hoạt động lặn biển.'),
    ('Đà Lạt', 'Đà Lạt, Việt Nam', 'núi', 'Thành phố cao nguyên với hồ Xuân Hương, thác nước, rừng thông và các vườn nông sản.'),
    ('Mũi Né', 'Mũi Né, Phan Thiết, Việt Nam', 'biển', 'Đồi cát, làng chài và bãi biển Mũi Né với điều kiện thuận lợi cho thể thao gió.'),
    ('Lý Sơn', 'Đảo Lý Sơn, Quảng Ngãi, Việt Nam', 'biển', 'Đảo núi lửa với cổng Tò Vò, miệng núi lửa, ruộng tỏi và di tích Hoàng Sa.'),
    ('Cù Lao Chàm', 'Cù Lao Chàm', 'biển', 'Cụm đảo và khu dự trữ sinh quyển thế giới với hoạt động tham quan biển và snorkeling.'),
    ('Măng Đen', 'Măng Đen, Kon Tum, Việt Nam', 'núi', 'Vùng cao nguyên có rừng thông, hồ, thác và các làng văn hóa ở Kon Plông.'),
    # South and Central Highlands
    ('Buôn Ma Thuột', 'Buôn Ma Thuột, Việt Nam', 'ẩm thực', 'Thủ phủ cà phê Việt Nam với Bảo tàng Thế giới Cà phê và văn hóa Tây Nguyên.'),
    ('Vũng Tàu', 'Vũng Tàu, Việt Nam', 'biển', 'Thành phố biển gần TP.HCM với Bãi Sau, Bãi Trước, Hải đăng và tượng Chúa Kitô.'),
    ('Phú Quốc', 'Đảo Phú Quốc, Việt Nam', 'biển', 'Đảo lớn nhất Việt Nam với bãi biển, vườn quốc gia, làng chài và các cơ sở nước mắm.'),
    ('Côn Đảo', 'Côn Đảo, Việt Nam', 'biển', 'Quần đảo có Vườn quốc gia Côn Đảo, bãi biển, rạn san hô và di tích lịch sử nhà tù.'),
    ('Cần Thơ', 'Cần Thơ, Việt Nam', 'ẩm thực', 'Trung tâm miền Tây với chợ nổi Cái Răng, bến Ninh Kiều và văn hóa ẩm thực sông nước.'),
    ('TP. Hồ Chí Minh', 'Thành phố Hồ Chí Minh, Việt Nam', 'ẩm thực', 'Đô thị lớn với Dinh Độc Lập, Bảo tàng Chứng tích Chiến tranh và nền ẩm thực đa vùng.'),
    ('Tây Ninh - Núi Bà Đen', 'Núi Bà Đen, Tây Ninh, Việt Nam', 'núi', 'Núi Bà Đen, các tuyến leo núi và quần thể văn hóa tâm linh ở Tây Ninh.'),
    ('Mỹ Tho', 'Mỹ Tho, Tiền Giang, Việt Nam', 'ẩm thực', 'Đô thị ven sông Tiền, điểm khởi hành tham quan cù lao và vườn trái cây miền Tây.'),
    ('Bến Tre', 'Bến Tre, Việt Nam', 'ẩm thực', 'Xứ dừa với kênh rạch, vườn dừa, làng nghề và các tuyến trải nghiệm sinh thái.'),
    ('Châu Đốc', 'Châu Đốc, An Giang, Việt Nam', 'thành phố', 'Vùng văn hóa đa dạng với Núi Sam, miếu Bà Chúa Xứ và chợ ẩm thực địa phương.'),
    ('Cà Mau', 'Cà Mau, Việt Nam', 'biển', 'Điểm cực Nam đất liền với Vườn quốc gia Mũi Cà Mau, rừng ngập mặn và hệ sinh thái ven biển.'),
]

REFERENCE_COSTS = {
    'Sa Pa': 2600000, 'Hà Giang': 2200000, 'Ninh Bình': 2500000,
    'Hạ Long': 4200000, 'Cát Bà': 3800000, 'Mộc Châu': 2100000,
    'Hà Nội': 3000000, 'Tam Đảo': 2400000, 'Ba Vì': 1900000,
    'Thác Bản Giốc (Cao Bằng)': 2300000, 'Mai Châu': 2000000, 'Pù Luông': 2300000,
    'Huế': 2700000, 'Đà Nẵng': 3900000, 'Hội An': 3600000,
    'Phong Nha - Kẻ Bàng': 2800000, 'Quy Nhơn': 3600000, 'Phú Yên': 3300000,
    'Nha Trang': 4300000, 'Đà Lạt': 3500000, 'Mũi Né': 3900000,
    'Lý Sơn': 4200000, 'Cù Lao Chàm': 4300000, 'Măng Đen': 2400000,
    'Buôn Ma Thuột': 2500000, 'Vũng Tàu': 3800000, 'Phú Quốc': 5800000,
    'Côn Đảo': 6000000, 'Cần Thơ': 2600000, 'TP. Hồ Chí Minh': 3400000,
    'Tây Ninh - Núi Bà Đen': 2300000, 'Mỹ Tho': 2100000, 'Bến Tre': 2000000,
    'Châu Đốc': 2400000, 'Cà Mau': 2300000,
}

TOURS = [
    ('Đông Bắc: Hà Giang - Cao Bằng - Hạ Long', 'Khám phá cao nguyên đá, thác Bản Giốc và di sản vịnh biển.', 'kham_pha', 5, 7890000, ['Hà Giang', 'Thác Bản Giốc (Cao Bằng)', 'Hạ Long']),
    ('Tây Bắc: Sa Pa - Mộc Châu - Mai Châu', 'Hành trình vùng cao qua bản làng, đồi chè và ruộng bậc thang.', 'van_hoa', 5, 6590000, ['Sa Pa', 'Mộc Châu', 'Mai Châu']),
    ('Di sản Bắc Bộ: Hà Nội - Ninh Bình - Hạ Long', 'Thủ đô, cố đô Hoa Lư và cảnh quan vịnh Hạ Long.', 'van_hoa', 5, 7290000, ['Hà Nội', 'Ninh Bình', 'Hạ Long']),
    ('Cuối tuần Tam Đảo - Ba Vì', 'Nghỉ ngắn ngày giữa rừng núi và khí hậu mát mẻ miền Bắc.', 'nghi_duong', 3, 3290000, ['Tam Đảo', 'Ba Vì']),
    ('Trekking Pù Luông - Mai Châu', 'Đi bộ qua ruộng bậc thang, bản làng và thung lũng.', 'mao_hiem', 4, 4290000, ['Pù Luông', 'Mai Châu']),
    ('Cố đô Huế - phố cổ Hội An - Đà Nẵng', 'Di sản, kiến trúc cổ và trải nghiệm thành phố biển miền Trung.', 'van_hoa', 5, 6990000, ['Huế', 'Hội An', 'Đà Nẵng']),
    ('Hang động Phong Nha - Huế', 'Khám phá hang động Quảng Bình và các di tích cố đô.', 'mao_hiem', 4, 5590000, ['Phong Nha - Kẻ Bàng', 'Huế']),
    ('Biển đảo Đà Nẵng - Cù Lao Chàm - Hội An', 'Kết hợp tắm biển, tham quan đảo và phố cổ.', 'nghi_duong', 4, 5790000, ['Đà Nẵng', 'Cù Lao Chàm', 'Hội An']),
    ('Quy Nhơn - Phú Yên', 'Cung đường ven biển qua Eo Gió, Kỳ Co và Gành Đá Đĩa.', 'kham_pha', 4, 4890000, ['Quy Nhơn', 'Phú Yên']),
    ('Nha Trang - Đà Lạt', 'Từ vịnh biển Nam Trung Bộ lên cao nguyên thông xanh.', 'ghep_doan', 5, 6290000, ['Nha Trang', 'Đà Lạt']),
    ('Nha Trang - Phú Yên nghỉ dưỡng biển', 'Nghỉ tại vịnh Nha Trang, tham quan đảo và trải nghiệm ẩm thực biển miền Trung.', 'nghi_duong', 3, 4590000, ['Nha Trang', 'Phú Yên']),
    ('Mũi Né - Phan Thiết khám phá', 'Đồi cát, làng chài và trải nghiệm thể thao biển.', 'mao_hiem', 3, 3790000, ['Mũi Né', 'Vũng Tàu']),
    ('Đảo Lý Sơn - di sản biển đảo', 'Tham quan đảo núi lửa và tìm hiểu lịch sử đội Hoàng Sa.', 'van_hoa', 4, 4990000, ['Lý Sơn', 'Đà Nẵng']),
    ('Cao nguyên Măng Đen - Buôn Ma Thuột', 'Rừng thông, thác nước, cà phê và văn hóa Tây Nguyên.', 'kham_pha', 5, 5690000, ['Măng Đen', 'Buôn Ma Thuột']),
    ('Đà Lạt - Măng Đen cao nguyên', 'Hành trình khí hậu cao nguyên và các cung đường rừng.', 'mao_hiem', 5, 5990000, ['Đà Lạt', 'Măng Đen']),
    ('Vũng Tàu - TP. Hồ Chí Minh', 'Thành phố biển và các địa danh lịch sử đô thị phía Nam.', 'rieng', 3, 3990000, ['Vũng Tàu', 'TP. Hồ Chí Minh']),
    ('Phú Quốc - Cần Thơ nghỉ dưỡng miền Tây', 'Bãi biển đảo ngọc, làng chài và trải nghiệm chợ nổi miền Tây.', 'nghi_duong', 4, 6990000, ['Phú Quốc', 'Cần Thơ']),
    ('Côn Đảo - Vũng Tàu lịch sử và biển', 'Di tích lịch sử Côn Đảo kết hợp nghỉ biển tại Vũng Tàu.', 'van_hoa', 4, 7390000, ['Côn Đảo', 'Vũng Tàu']),
    ('Cần Thơ - Mỹ Tho - Bến Tre', 'Chợ nổi, cù lao và trải nghiệm sinh thái sông nước.', 'am_thuc', 4, 4590000, ['Cần Thơ', 'Mỹ Tho', 'Bến Tre']),
    ('Châu Đốc - Cần Thơ', 'Văn hóa vùng biên, Núi Sam và chợ nổi miền Tây.', 'van_hoa', 4, 4290000, ['Châu Đốc', 'Cần Thơ']),
    ('Cà Mau - miền cực Nam', 'Rừng ngập mặn, Đất Mũi và hệ sinh thái ven biển.', 'kham_pha', 4, 4990000, ['Cà Mau', 'Cần Thơ']),
    ('Tây Ninh - Núi Bà Đen', 'Chinh phục núi và tham quan các điểm văn hóa Tây Ninh.', 'mao_hiem', 3, 3290000, ['Tây Ninh - Núi Bà Đen', 'TP. Hồ Chí Minh']),
    ('Ẩm thực Hà Nội - Huế - TP.HCM', 'Thưởng thức những nét ẩm thực đặc trưng của ba miền.', 'am_thuc', 5, 7490000, ['Hà Nội', 'Huế', 'TP. Hồ Chí Minh']),
    ('Đảo miền Trung: Cù Lao Chàm - Lý Sơn', 'Trải nghiệm hai cụm đảo và văn hóa biển miền Trung.', 'ghep_doan', 5, 6890000, ['Cù Lao Chàm', 'Lý Sơn']),
    ('Biển Nam Trung Bộ: Quy Nhơn - Nha Trang - Mũi Né', 'Khám phá các bãi biển và cung đường ven biển miền Trung.', 'rieng', 5, 7990000, ['Quy Nhơn', 'Nha Trang', 'Mũi Né']),
]


def normalize(value):
    decomposed = unicodedata.normalize('NFKD', value.casefold())
    return ' '.join(''.join(char for char in decomposed if not unicodedata.combining(char)).replace('-', ' ').split())


class Command(BaseCommand):
    help = 'Seed 35 Vietnam destinations, nearby OSM lodging and 25 multi-stop tours via the existing lookup API.'

    def add_arguments(self, parser):
        parser.add_argument('--delay', type=float, default=1.0, help='Seconds between lookup endpoint calls (default: 1).')
        existing_group = parser.add_mutually_exclusive_group()
        existing_group.add_argument(
            '--skip-existing', dest='skip_existing', action='store_true', default=True,
            help='Skip lookup for destinations already in the database (default).',
        )
        existing_group.add_argument(
            '--no-skip-existing', dest='skip_existing', action='store_false',
            help='Refresh lookup data for destinations already in the database.',
        )

    def handle(self, *args, **options):
        if len(DESTINATIONS) != 35 or len(TOURS) != 25:
            raise CommandError('The extended seed catalog must contain exactly 35 destinations and 25 tours.')
        delay = max(0.5, min(1.0, options['delay']))
        endpoint = 'http://127.0.0.1:8000/api/destinations/lookup/'
        session = requests.Session()
        session.headers['User-Agent'] = 'DuLichThongMinhSeed/1.0'
        last_lookup_at = 0.0

        def lookup(query, include_image, image_query=None):
            nonlocal last_lookup_at
            wait = delay - (time.monotonic() - last_lookup_at)
            if last_lookup_at and wait > 0:
                time.sleep(wait)
            params = {'q': query, 'include_image': str(include_image).lower()}
            if image_query:
                params['image_query'] = image_query
            response = session.get(endpoint, params=params, timeout=90)
            last_lookup_at = time.monotonic()
            response.raise_for_status()
            results = response.json().get('results', [])
            return [item for item in results if item.get('source') == 'nominatim']

        destination_payloads = []
        destination_by_name = {}
        self.stdout.write(f'Lookup {len(DESTINATIONS)} real destinations via {endpoint}')
        for index, (name, query, category, description) in enumerate(DESTINATIONS, 1):
            existing = Destination.objects.filter(name=name).first()
            if existing and options['skip_existing']:
                destination = existing
                reference_cost = REFERENCE_COSTS[name]
                if not destination.reference_cost:
                    Destination.objects.filter(pk=destination.pk).update(reference_cost=reference_cost)
                    destination.reference_cost = reference_cost
                destination_payloads.append({
                    'name': name,
                    'description': destination.description,
                    'category': destination.category,
                    'latitude': destination.latitude,
                    'longitude': destination.longitude,
                    'image_url': destination.image_url,
                    'address': destination.address,
                    'reference_cost': destination.reference_cost,
                    'rating': destination.rating,
                })
                destination_by_name[name] = destination
                self.stdout.write(f'[{index:02}/35] Đã có: {name} (bỏ qua lookup)')
                self.stdout.flush()
                continue

            image_query = name.split('(')[0].strip()
            if name == 'Tây Ninh - Núi Bà Đen':
                image_query = 'Núi Bà Đen'
            elif name == 'Phong Nha - Kẻ Bàng':
                image_query = 'Phong Nha'
            elif name == 'TP. Hồ Chí Minh':
                image_query = 'Ho Chi Minh City'
            ascii_name = normalize(name)
            image_queries = list(dict.fromkeys((image_query, f'{ascii_name} Vietnam', f'{ascii_name} travel')))
            try:
                candidates = []
                selected = None
                image_url = ''
                for photo_query in image_queries:
                    results = lookup(query, True, image_query=photo_query)
                    candidates = [
                        item for item in results
                        if 8.0 <= float(item.get('latitude') or 0) <= 24.5
                        and 102.0 <= float(item.get('longitude') or 0) <= 110.0
                        and float(item.get('latitude') or 0) != 0
                        and float(item.get('longitude') or 0) != 0
                    ]
                    if candidates:
                        target = normalize(name)
                        candidates.sort(key=lambda item: (0 if target in normalize(item.get('full_name', '')) else 1, len(normalize(item.get('full_name', '')))))
                        image_url = candidates[0].get('image_url') or ''
                        if image_url.startswith('https://images.unsplash.com/') and 'photo-1507525428034-b723cf961d3e' not in image_url:
                            selected = candidates[0]
                            break
                if not candidates:
                    raise ValueError(f'Lookup returned no valid Vietnam coordinates ({query}).')
                if selected is None:
                    raise ValueError('Lookup did not return a destination-specific Unsplash image.')
            except Exception as exc:
                logger.warning('Bỏ qua điểm đến %s do lookup lỗi: %s', name, exc, exc_info=True)
                self.stdout.write(self.style.WARNING(f'[{index:02}/35] Bỏ qua: {name} — {exc}'))
                self.stdout.flush()
                continue

            payload = {
                'name': name,
                'description': description,
                'category': category,
                'latitude': float(selected['latitude']),
                'longitude': float(selected['longitude']),
                'image_url': image_url,
                'rating': 4.3 + ((index % 7) / 10),
                'lookup_full_name': selected.get('full_name', ''),
                'address': selected.get('full_name', ''),
                'reference_cost': REFERENCE_COSTS[name],
            }
            values = {key: payload[key] for key in ('description', 'category', 'latitude', 'longitude', 'image_url', 'rating', 'address', 'reference_cost')}
            destination, _ = Destination.objects.update_or_create(name=name, defaults=values)
            destination_payloads.append(payload)
            destination_by_name[name] = destination
            self.stdout.write(f'[{index:02}/35] Đã ghi: {name}')
            self.stdout.flush()

        amenity_keys = set(Amenity.objects.values_list('key', flat=True))
        if not {'wifi', 'dieu_hoa', 'bua_sang', 'ban_cong', 'huong_bien', 'ho_boi'} <= amenity_keys:
            raise CommandError('Demo accommodation amenities must match keys in the Amenity table.')

        name_styles = {
            'biển': {
                'prefixes': ['Sóng Xanh', 'Gió Biển', 'San Hô', 'Bình Minh', 'Cát Trắng', 'Nắng Mai', 'Vòm Dừa', 'Bờ Cát'],
                'styles': [('Homestay', 'homestay'), ('Lodge', 'hotel'), ('Nhà Nghỉ', 'hotel'), ('Khu Lưu Trú', 'hotel'), ('Khu Nghỉ Dưỡng', 'hotel'), ('Biệt Thự', 'hotel'), ('Nhà Vườn', 'homestay'), ('Nhà Gỗ', 'homestay')],
                'amenities': ['wifi', 'dieu_hoa', 'huong_bien', 'ho_boi', 'bua_sang'],
                'base_price': 1_350_000,
            },
            'núi': {
                'prefixes': ['Sương Mai', 'Mây Núi', 'Rừng Thông', 'Thung Mây', 'Dốc Gió', 'Suối Nhỏ', 'Nếp Nhà', 'Đồi Mơ'],
                'styles': [('Homestay', 'homestay'), ('Lodge', 'hotel'), ('Nhà Nghỉ', 'hotel'), ('Nhà Sàn', 'homestay'), ('Khu Nghỉ Dưỡng', 'hotel'), ('Biệt Thự', 'hotel'), ('Nhà Gỗ', 'homestay'), ('Vườn Mây', 'homestay')],
                'amenities': ['wifi', 'dieu_hoa', 'bua_sang', 'ban_cong'],
                'base_price': 780_000,
            },
            'thành phố': {
                'prefixes': ['Ngõ Nhỏ', 'Hiên Phố', 'An Nhiên', 'Phố Mộc', 'Ban Công', 'Mái Ngói', 'Góc Phố', 'Nắng Nhà'],
                'styles': [('Homestay', 'homestay'), ('Lodge', 'hotel'), ('Nhà Nghỉ', 'hotel'), ('Khu Lưu Trú', 'hotel'), ('Khu Nghỉ Dưỡng', 'hotel'), ('Biệt Thự', 'hotel'), ('Nhà Vườn', 'homestay'), ('Nhà Gỗ', 'homestay')],
                'amenities': ['wifi', 'dieu_hoa', 'bua_sang', 'ban_cong'],
                'base_price': 1_200_000,
            },
            'ẩm thực': {
                'prefixes': ['Bếp Quê', 'Hương Vị', 'Miệt Vườn', 'Vườn Nhà', 'Bến Nước', 'Lá Dừa', 'Vị Quê', 'Vườn Thơm'],
                'styles': [('Homestay', 'homestay'), ('Lodge', 'hotel'), ('Nhà Nghỉ', 'hotel'), ('Nhà Vườn', 'homestay'), ('Khu Nghỉ Dưỡng', 'hotel'), ('Biệt Thự', 'hotel'), ('Nhà Gỗ', 'homestay'), ('Vườn Xanh', 'homestay')],
                'amenities': ['wifi', 'dieu_hoa', 'bua_sang', 'ban_cong'],
                'base_price': 900_000,
            },
        }
        # Keep generated stays on land for small islands and narrow coastal areas.
        radius_caps_km = {
            'Côn Đảo': 8,
            'Lý Sơn': 4,
            'Cù Lao Chàm': 3,
            'Cát Bà': 10,
            'Phú Quốc': 25,
        }
        coastal_landward_names = {
            name for name, _, category, _ in DESTINATIONS if category == 'biển'
        }
        self.stdout.write('Tạo chỗ ở demo với tọa độ giả lập quanh từng điểm đến')
        for index, payload in enumerate(destination_payloads, 1):
            destination = destination_by_name[payload['name']]
            config = name_styles.get(destination.category, name_styles['thành phố'])
            max_radius = radius_caps_km.get(destination.name, 40)
            # Keep three stays within 5 km and use the fourth to populate the 10 km interval.
            distance_bands = [(min(0.6, max_radius), min(4.5, max_radius))] * 3
            if max_radius > 5:
                distance_bands.append((5.5, min(9, max_radius)))
            else:
                distance_bands.append((min(0.6, max_radius), max_radius))
            # Three new stays populate the 20, 30, and 50 km intervals where geography allows.
            for lower, upper in ((14, 18), (22, 29), (32, 38)):
                if lower < max_radius:
                    distance_bands.append((lower, min(upper, max_radius)))

            # Remove only records generated by the previous OpenStreetMap-based version.
            Accommodation.objects.filter(
                destination=destination,
                description__startswith='Địa điểm lưu trú OpenStreetMap:',
            ).delete()

            amenity_list = list(dict.fromkeys(config['amenities']))
            accommodation_names = []
            for lodging_index, (band_min, band_max) in enumerate(distance_bands):
                prefix = config['prefixes'][lodging_index % len(config['prefixes'])]
                style, accommodation_category = config['styles'][lodging_index % len(config['styles'])]
                lodging_name = f'{prefix} {style} {destination.name}'
                accommodation_names.append(lodging_name)

                lodging_rng = random.Random(f'demo-lodging:{destination.name}:{lodging_index}')
                distance_km = lodging_rng.uniform(band_min, band_max)
                if destination.name == 'Phú Quốc':
                    # Keep these locations along the island's north-south axis.
                    bearing = lodging_rng.choice((0.0, math.pi)) + lodging_rng.uniform(-0.12, 0.12)
                elif destination.name in coastal_landward_names:
                    # A westward bearing generally points inland from Vietnam's east coast.
                    bearing = math.radians(270) + lodging_rng.uniform(-0.55, 0.55)
                else:
                    bearing = lodging_rng.uniform(0.0, 2.0 * math.pi)
                dlat = distance_km * math.cos(bearing) / 111.0
                cos_lat = max(0.01, math.cos(math.radians(destination.latitude)))
                dlon = distance_km * math.sin(bearing) / (111.0 * cos_lat)
                lodging_latitude = destination.latitude + dlat
                lodging_longitude = destination.longitude + dlon

                accommodation, _ = Accommodation.objects.update_or_create(
                    destination=destination,
                    name=lodging_name,
                    defaults={
                        'description': f'Cơ sở lưu trú minh họa do quản trị viên biên soạn tại khu vực {destination.name}.',
                        'category': accommodation_category,
                        'latitude': lodging_latitude,
                        'longitude': lodging_longitude,
                        'rating': round(lodging_rng.uniform(3.8, 4.9), 1),
                    },
                )

                room_count = lodging_rng.randint(1, 2)
                room_specs = [
                    ('Phòng tiêu chuẩn', 1.0, 5, amenity_list[:3]),
                    ('Phòng gia đình', 1.65, 3, amenity_list),
                ]
                for room_name, price_factor, stock, amenities in room_specs[:room_count]:
                    RoomType.objects.update_or_create(
                        accommodation=accommodation,
                        name=room_name,
                        defaults={
                            'base_price': int(config['base_price'] * price_factor),
                            'stock': stock,
                            'amenities': amenities,
                        },
                    )

            self.stdout.write(f'[{index:02}/35] Đã tạo chỗ ở: {destination.name} ({len(distance_bands)})')
            self.stdout.flush()

        seedable_tours = []
        for tour_data in TOURS:
            missing_stops = [stop_name for stop_name in tour_data[5] if stop_name not in destination_by_name]
            if missing_stops:
                self.stdout.write(self.style.WARNING(
                    f'Bỏ qua tour {tour_data[0]} vì điểm đến chưa được seed: {", ".join(missing_stops)}'
                ))
                continue
            seedable_tours.append(tour_data)

        with transaction.atomic():
            TourStop.objects.filter(tour__name__in=[row[0] for row in seedable_tours]).delete()
            today = date.today()
            for name, description, category, duration, price, stop_names in seedable_tours:
                tour, _ = Tour.objects.update_or_create(
                    name=name,
                    defaults={
                        'description': description,
                        'category': category,
                        'duration_days': duration,
                        'price_adult': price,
                        'price_child': int(price * 0.7),
                        'single_room_supplement': 450_000,
                        'min_age': 5,
                        'included_services': ['Lưu trú theo chương trình', 'Xe du lịch', 'Hướng dẫn viên địa phương'],
                        'excluded_services': ['Chi phí cá nhân', 'Đồ uống ngoài chương trình'],
                        'cancellation_policy': 'Hủy trước 7 ngày hoàn 100%; hủy trước 3 ngày hoàn 50%.',
                        'price_per_person': price,
                        'cover_image_url': destination_by_name[stop_names[0]].image_url,
                        'is_active': True,
                    },
                )
                for day_number, stop_name in enumerate(stop_names, 1):
                    TourStop.objects.create(
                        tour=tour,
                        destination=destination_by_name[stop_name],
                        day_number=day_number,
                        note=f'Tham quan {stop_name} và trải nghiệm văn hóa, cảnh quan địa phương.',
                    )
                tour.departures.filter(departure_date__lt=today).delete()
                for offset in (10, 24, 38):
                    TourDeparture.objects.update_or_create(
                        tour=tour,
                        departure_date=today + timedelta(days=offset),
                        defaults={'slots_total': 18, 'is_cancelled': False},
                    )

        destinations_count = Destination.objects.filter(name__in=destination_by_name).count()
        accommodations_count = Accommodation.objects.filter(destination__in=destination_by_name.values()).count()
        tours_count = Tour.objects.filter(name__in=[row[0] for row in seedable_tours], is_active=True).count()
        departures_count = TourDeparture.objects.filter(tour__name__in=[row[0] for row in seedable_tours], departure_date__range=(today, today + timedelta(days=60)), is_cancelled=False).count()
        self.stdout.write(self.style.SUCCESS(
            f'Seed complete: {destinations_count} destinations, {accommodations_count} accommodations, '
            f'{tours_count} tours, {departures_count} departures.'
        ))
