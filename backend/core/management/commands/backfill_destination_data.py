import logging
import os
import time

import requests
from django.core.management.base import BaseCommand

from core.management.commands.seed_extended_travel_data import DESTINATIONS, REFERENCE_COSTS
from core.models import Destination


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Điền địa chỉ từ lookup Nominatim và chi phí tham khảo cho các điểm đến đã seed.'

    def handle(self, *args, **options):
        base_url = os.getenv('BASE_URL', 'http://127.0.0.1:8000').rstrip('/')
        endpoint = os.getenv('DESTINATION_LOOKUP_URL', f'{base_url}/api/destinations/lookup/')
        session = requests.Session()
        session.headers['Accept-Language'] = 'vi'
        updated = 0
        lookup_count = 0

        for name, query, _category, _description in DESTINATIONS:
            destination = Destination.objects.filter(name=name).first()
            if destination is None:
                self.stdout.write(self.style.WARNING(f'Bỏ qua, chưa có trong cơ sở dữ liệu: {name}'))
                continue

            changed_fields = []
            reference_cost = REFERENCE_COSTS[name]
            if destination.reference_cost != reference_cost:
                destination.reference_cost = reference_cost
                changed_fields.append('reference_cost')

            if not destination.address:
                if lookup_count:
                    time.sleep(1)
                lookup_count += 1
                try:
                    response = session.get(
                        endpoint,
                        params={'q': query, 'include_image': 'false'},
                        timeout=15,
                    )
                    response.raise_for_status()
                    places = response.json().get('results', [])
                    place = next((item for item in places if item.get('source') == 'nominatim' and item.get('full_name')), None)
                    if place:
                        destination.address = place['full_name'][:300]
                        changed_fields.append('address')
                    else:
                        logger.warning('backfill_destination_data: Nominatim returned no place for %s.', name)
                except (requests.RequestException, ValueError, TypeError) as exc:
                    logger.warning('backfill_destination_data: lookup failed for %s: %s', name, exc)

            if changed_fields:
                destination.save(update_fields=changed_fields)
                updated += 1
            self.stdout.write(f'Đã xử lý: {name}')

        self.stdout.write(self.style.SUCCESS(f'Hoàn tất: cập nhật {updated} điểm đến; thực hiện {lookup_count} lượt lookup.'))
