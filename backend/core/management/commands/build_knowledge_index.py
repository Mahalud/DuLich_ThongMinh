from django.core.management.base import BaseCommand

from core.rag import build_knowledge_index
from core.models import KnowledgeChunk


class Command(BaseCommand):
    help = 'Build or update the public travel knowledge index.'

    def handle(self, *args, **options):
        result = build_knowledge_index()
        for source_type, _label in KnowledgeChunk.SOURCE_TYPES:
            self.stdout.write(f'{source_type}: {result["counts"].get(source_type, 0)}')
        self.stdout.write(f'Embeddings computed: {result["embedded"]}')
        self.stdout.write(f'Orphan chunks deleted: {result["deleted"]}')
