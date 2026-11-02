from django.core.management.base import BaseCommand

from core.embedding import destination_embedding_text, encode_text
from core.models import Destination


class Command(BaseCommand):
    help = 'Tính lại Sentence-BERT embedding cho mọi điểm đến hiện có.'

    def handle(self, *args, **options):
        destinations = Destination.objects.all().order_by('id')
        total = destinations.count()
        for index, destination in enumerate(destinations.iterator(), start=1):
            vector = encode_text(destination_embedding_text(destination))
            Destination.objects.filter(pk=destination.pk).update(embedding_cache=vector)
            self.stdout.write(f'[{index}/{total}] Đã cập nhật embedding: {destination.name}')
        self.stdout.write(self.style.SUCCESS(f'Đã tính lại embedding cho {total} điểm đến.'))
