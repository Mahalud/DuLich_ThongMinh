import base64
import hashlib
import os
from datetime import date

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

User = get_user_model()


def get_fernet_key():
    env_key = os.getenv('FERNET_KEY')
    if env_key:
        candidate = env_key.strip()
        if len(candidate) >= 32:
            if len(candidate) == 44 and candidate.endswith('='):
                return candidate.encode()
            return base64.urlsafe_b64encode(candidate.encode().ljust(32, b'0')[:32])
    return base64.urlsafe_b64encode(hashlib.sha256(settings.SECRET_KEY.encode()).digest())


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    travel_preferences = models.JSONField(default=list, blank=True)
    budget_estimate = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    free_text = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.username} profile'


class SearchHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='search_history')
    query = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username}: {self.query[:40]}'


class Destination(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=[
        ('biển', 'Biển'),
        ('núi', 'Núi'),
        ('thành phố', 'Thành phố'),
        ('ẩm thực', 'Ẩm thực'),
    ])
    latitude = models.FloatField(default=0.0)
    longitude = models.FloatField(default=0.0)
    image_url = models.URLField(blank=True, default='')
    rating = models.FloatField(default=0.0)
    embedding_cache = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        source_text = ' '.join([self.name, self.description, self.category])
        should_refresh_embedding = self.embedding_cache is None
        if self.pk:
            previous = type(self).objects.filter(pk=self.pk).values('name', 'description', 'category').first()
            should_refresh_embedding = should_refresh_embedding or bool(previous and source_text != ' '.join([
                previous['name'], previous['description'], previous['category'],
            ]))
        if should_refresh_embedding:
            from .embedding import encode_text

            self.embedding_cache = encode_text(source_text)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Accommodation(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(default='')
    category = models.CharField(max_length=50, choices=[
        ('hotel', 'Hotel'),
        ('homestay', 'Homestay'),
    ], default='hotel')
    latitude = models.FloatField(default=0.0)
    longitude = models.FloatField(default=0.0)
    rating = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class RoomType(models.Model):
    accommodation = models.ForeignKey(Accommodation, on_delete=models.CASCADE, related_name='room_types')
    name = models.CharField(max_length=50)
    base_price = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    stock = models.PositiveIntegerField(default=1)
    amenities = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f'{self.accommodation.name} - {self.name}'


class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE, related_name='bookings')
    check_in = models.DateField()
    check_out = models.DateField()
    guest_phone = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    refund_amount = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def fernet_key(self):
        return get_fernet_key()

    def clean(self):
        super().clean()

        if isinstance(self.check_in, str):
            self.check_in = date.fromisoformat(self.check_in)
        if isinstance(self.check_out, str):
            self.check_out = date.fromisoformat(self.check_out)

        if self.check_in < timezone.localdate():
            raise ValidationError({'check_in': 'Ngày nhận phải lớn hơn hoặc bằng hôm nay.'})
        if self.check_out <= self.check_in:
            raise ValidationError({'check_out': 'Ngày trả phải sau ngày nhận.'})

        if self.user_id and self.room_type_id:
            overlap_count = Booking.objects.filter(
                room_type=self.room_type,
                status__in=['pending', 'confirmed'],
            ).exclude(pk=self.pk).filter(
                check_in__lt=self.check_out,
                check_out__gt=self.check_in,
            ).count()
            if overlap_count >= self.room_type.stock:
                raise ValidationError('Không còn phòng trống cho khoảng thời gian này.')

    def save(self, *args, **kwargs):
        self.full_clean()
        encrypted_phone = self._encrypt_phone(self.guest_phone)
        self.guest_phone = encrypted_phone
        super().save(*args, **kwargs)

    def decrypt_guest_phone(self):
        if not self.guest_phone:
            return ''
        try:
            cipher = Fernet(self.fernet_key)
            return cipher.decrypt(self.guest_phone.encode()).decode()
        except (InvalidToken, ValueError, TypeError):
            return self.guest_phone

    @staticmethod
    def _encrypt_phone(phone):
        if not phone:
            return ''
        cipher = Fernet(get_fernet_key())
        return cipher.encrypt(phone.encode()).decode()

    @classmethod
    def can_create_for_room(cls, room_type, check_in, check_out, exclude_booking=None):
        overlap_count = cls.objects.filter(
            room_type=room_type,
            status__in=['pending', 'confirmed'],
        )
        if exclude_booking:
            overlap_count = overlap_count.exclude(pk=exclude_booking.pk)
        overlap_count = overlap_count.filter(
            check_in__lt=check_out,
            check_out__gt=check_in,
        ).count()
        return overlap_count < room_type.stock

    def cancel_booking(self, refund_amount=0):
        self.status = 'cancelled'
        self.refund_amount = refund_amount
        self.save(update_fields=['status', 'refund_amount'])
        return self

    def __str__(self):
        return f'{self.user.username} - {self.room_type}'


class AccommodationReview(models.Model):
    accommodation = models.ForeignKey(Accommodation, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(default=5)
    comment = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} review for {self.accommodation.name}'


class ChatMessage(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.sender.username} -> {self.receiver.username}: {self.content[:40]}'

