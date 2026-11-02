from django.core.management.base import BaseCommand
from django.contrib.gis.db.models.functions import Distance

from core.models import Accommodation, Destination


class Command(BaseCommand):
    help = 'Báo cáo số chỗ ở quanh từng điểm đến theo các bán kính dùng trong giao diện.'

    radii_km = (5, 10, 20, 30, 50)

    def handle(self, *args, **options):
        for destination in Destination.objects.order_by('name'):
            if destination.vi_tri is None:
                self.stdout.write(f'{destination.name}: chưa có tọa độ')
                continue

            # Giữ cùng phép Distance và cách lọc mét như API accommodations_near_destination.
            nearby = Accommodation.objects.filter(vi_tri__isnull=False).annotate(
                distance_m=Distance('vi_tri', destination.vi_tri, spheroid=False)
            )
            counts = [
                nearby.filter(distance_m__lte=radius * 1000).count()
                for radius in self.radii_km
            ]
            summary = ' | '.join(
                f'{radius} km: {count}'
                for radius, count in zip(self.radii_km, counts)
            )
            self.stdout.write(f'{destination.name}: {summary}')
