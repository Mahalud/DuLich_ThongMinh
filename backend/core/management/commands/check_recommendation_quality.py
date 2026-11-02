from datetime import date

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from core.embedding import encode_text, expand_preferences
from core.models import Destination
from core.views import _cosine_similarity, _recommendation_results


SAMPLE_QUERIES = (
    'biển', 'núi', 'ẩm thực', 'văn hóa lịch sử', 'nghỉ dưỡng', 'đi biển ăn hải sản',
    'xyz', 'bóng đá', 'lập trình', 'asdfgh',
)


class Command(BaseCommand):
    help = 'In top 8 kết quả cho các sở thích mẫu từ một vị trí xuất phát.'

    def add_arguments(self, parser):
        parser.add_argument('--latitude', type=float, required=True, help='Vĩ độ điểm xuất phát.')
        parser.add_argument('--longitude', type=float, required=True, help='Kinh độ điểm xuất phát.')
        parser.add_argument('--budget', type=int, default=5000000, help='Ngân sách tham khảo VND (mặc định 5.000.000).')
        parser.add_argument('--travel-date', default=date.today().isoformat(), help='Ngày đi ISO (mặc định hôm nay).')

    def handle(self, *args, **options):
        if not -90 <= options['latitude'] <= 90 or not -180 <= options['longitude'] <= 180:
            raise CommandError('Tọa độ xuất phát nằm ngoài phạm vi hợp lệ.')
        try:
            travel_date = date.fromisoformat(options['travel_date'])
        except ValueError as exc:
            raise CommandError('--travel-date cần có định dạng YYYY-MM-DD.') from exc

        for query in SAMPLE_QUERIES:
            query_vector = encode_text(expand_preferences(query))
            destinations = list(Destination.objects.exclude(embedding_cache__isnull=True))
            if not destinations:
                raise CommandError('Chưa có embedding nào để đo cosine; hãy chạy lệnh tính embedding riêng khi được phép.')
            maximum_cosine = max(
                _cosine_similarity(query_vector, destination.embedding_cache)
                for destination in destinations
            )
            self.stdout.write(f'\nSở thích: {query}')
            self.stdout.write(f'Cosine cao nhất: {maximum_cosine:.6f} (trên {len(destinations)} điểm đến có embedding)')
            self.stdout.write(f'PREFERENCE_MATCH_MIN: {settings.PREFERENCE_MATCH_MIN:.6f}')
            self.stdout.write('Tên | Loại | Sở thích | Thời tiết | Ngân sách | Khoảng cách')
            results = _recommendation_results(
                query, options['budget'], options['latitude'], options['longitude'], travel_date, 8,
            )
            for item in results:
                distance = '—' if item['distance_score'] is None else f"{item['distance_score']:.3f}"
                self.stdout.write(
                    f"{item['name']} | {item['category']} | {item['preference_score']:.3f} "
                    f"(raw {item['preference_raw']:.3f}) | {item['weather_score']:.3f} | "
                    f"{item['budget_score']:.3f} | {distance}"
                )
