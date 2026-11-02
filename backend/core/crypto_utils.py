import base64
import hashlib
import os

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings


def get_fernet_key() -> bytes:
    env_key = os.getenv('FERNET_KEY')
    if env_key:
        candidate = env_key.strip()
        if len(candidate) >= 32:
            if len(candidate) == 44 and candidate.endswith('='):
                return candidate.encode()
            return base64.urlsafe_b64encode(candidate.encode().ljust(32, b'0')[:32])
    return base64.urlsafe_b64encode(hashlib.sha256(settings.SECRET_KEY.encode()).digest())


def encrypt_phone(phone: str) -> str:
    if not phone:
        return ''
    phone_str = str(phone).strip()
    key = get_fernet_key()
    # Check if already encrypted with the current key
    try:
        cipher = Fernet(key)
        decrypted = cipher.decrypt(phone_str.encode()).decode()
        if decrypted:
            return phone_str
    except Exception:
        pass
    cipher = Fernet(key)
    return cipher.encrypt(phone_str.encode()).decode()


def decrypt_phone(encrypted_phone: str) -> str:
    if not encrypted_phone:
        return ''
    phone_str = str(encrypted_phone).strip()
    try:
        cipher = Fernet(get_fernet_key())
        return cipher.decrypt(phone_str.encode()).decode()
    except (InvalidToken, ValueError, TypeError):
        return phone_str
