"""Shared authentication throttling and Vietnamese password validation errors."""

import hashlib
import logging
import math
import time

from django.contrib.auth.password_validation import validate_password
from django.core.cache import cache
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

PASSWORD_ERROR_MESSAGES = {
    'password_too_short': 'Mật khẩu phải có ít nhất 8 ký tự.',
    'password_too_common': 'Mật khẩu quá phổ biến. Hãy chọn mật khẩu khó đoán hơn.',
    'password_entirely_numeric': 'Mật khẩu không được chỉ gồm chữ số.',
    'password_too_similar': 'Mật khẩu quá giống thông tin tài khoản.',
}


def password_errors(password, user):
    try:
        validate_password(password, user=user)
    except ValidationError as exc:
        return [PASSWORD_ERROR_MESSAGES.get(error.code, error.message) for error in exc.error_list]
    return []


def throttle_key(action, kind, value):
    digest = hashlib.sha256(str(value).strip().casefold().encode('utf-8')).hexdigest()
    return f'auth-throttle:v1:{action}:{kind}:{digest}'


def throttle_remaining(keys, limit):
    """Seconds until any exhausted fixed-window counter becomes available."""
    try:
        now = time.time()
        waits = [max(1, math.ceil(float(cache.get(f'{key}:end', now + 1)) - now))
                 for key in keys if int(cache.get(key, 0) or 0) >= limit]
        return max(waits, default=0)
    except Exception:
        logger.warning('Không đọc được bộ đệm giới hạn xác thực.', exc_info=True)
        return 0


def record_attempt(keys, window_seconds):
    try:
        for key in keys:
            if cache.add(key, 1, timeout=window_seconds):
                cache.set(f'{key}:end', time.time() + window_seconds, timeout=window_seconds)
            else:
                cache.incr(key)
    except Exception:
        logger.warning('Không ghi được bộ đệm giới hạn xác thực.', exc_info=True)
