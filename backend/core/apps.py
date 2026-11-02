import logging
import os
import sys
import threading
from pathlib import Path

from django.apps import AppConfig


logger = logging.getLogger(__name__)
_warmup_lock = threading.Lock()
_warmup_started = False


def should_warmup_model(argv=None, environ=None):
    """Warm the web process only; management commands and workers stay lazy."""
    argv = list(sys.argv if argv is None else argv)
    environ = os.environ if environ is None else environ
    process_path = Path(argv[0]) if argv else Path('')
    executable = process_path.name.lower()
    command = argv[1].lower() if len(argv) > 1 else ''

    if executable in {'manage.py', 'django-admin', 'django-admin.py'}:
        if command != 'runserver':
            return False
        # The parent process of Django's autoreloader never serves requests.
        return '--noreload' in argv or environ.get('RUN_MAIN') == 'true'
    if executable.startswith('celery'):
        return False
    if executable.startswith(('daphne', 'uvicorn')) or any(
        part.lower() in {'daphne', 'uvicorn'} for part in process_path.parts
    ):
        return True
    return environ.get('MODEL_WARMUP') == '1'


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        """Load the embedding model once in the actual request-serving process."""
        global _warmup_started

        if not should_warmup_model():
            return

        with _warmup_lock:
            if _warmup_started:
                return
            _warmup_started = True

        try:
            from .embedding import encode_text

            logger.info('BẮT ĐẦU warm-up Sentence-BERT khi khởi động ứng dụng')
            encode_text('warm-up')
            logger.info('XONG warm-up Sentence-BERT khi khởi động ứng dụng')
        except Exception:
            logger.exception('Warm-up Sentence-BERT thất bại')
            raise
