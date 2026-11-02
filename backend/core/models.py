from datetime import date
import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.exceptions import ValidationError
from django.contrib.gis.db import models
from django.contrib.gis.geos import Point
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

from .crypto_utils import decrypt_phone, encrypt_phone, get_fernet_key

User = get_user_model()

AMENITY_ICON_CHOICES = [(name, name) for name in (
    'wifi', 'dieu_hoa', 'bon_tam', 'huong_bien', 'ho_boi', 'bua_sang',
    'do_xe', 'thang_may', 'bep', 'giat_ui', 'tivi', 'ban_cong',
)]


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    is_demo = models.BooleanField(default=False)
    travel_preferences = models.JSONField(default=list, blank=True)
    budget_estimate = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    weather_preference = models.CharField(max_length=12, choices=[
        ('balanced', 'Mặc định'), ('cool', 'Mát mẻ'), ('warm', 'Nắng ấm'), ('dry', 'Ít mưa'),
    ], default='balanced')
    free_text = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.username} profile'


class SearchHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='search_history')
    query = models.TextField()
    preferences = models.JSONField(default=list, blank=True)
    budget_estimate = models.PositiveBigIntegerField(default=0)
    weather_preference = models.CharField(max_length=12, choices=[
        ('balanced', 'Mặc định'), ('cool', 'Mát mẻ'), ('warm', 'Nắng ấm'), ('dry', 'Ít mưa'),
    ], default='balanced')
    latitude = models.FloatField(default=0)
    longitude = models.FloatField(default=0)
    travel_date = models.DateField(null=True, blank=True)
    top_n = models.PositiveSmallIntegerField(default=5)
    destination = models.ForeignKey('Destination', on_delete=models.SET_NULL, null=True, blank=True, related_name='search_history')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username}: {self.query[:40]}'


class SitePage(models.Model):
    slug = models.SlugField(max_length=120, unique=True)
    title = models.CharField(max_length=200)
    cover_image_url = models.URLField(max_length=600, blank=True, default='')
    intro = models.TextField(blank=True, default='')
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='updated_site_pages',
    )

    class Meta:
        ordering = ['slug']

    def __str__(self):
        return self.title


class SitePageSection(models.Model):
    LAYOUT_CHOICES = [
        ('text', 'Văn bản'),
        ('image_left', 'Ảnh trái'),
        ('image_right', 'Ảnh phải'),
        ('cards', 'Thẻ'),
    ]
    page = models.ForeignKey(SitePage, on_delete=models.CASCADE, related_name='sections')
    order = models.PositiveIntegerField(default=0)
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True, default='')
    image_url = models.URLField(max_length=600, blank=True, default='')
    layout = models.CharField(max_length=16, choices=LAYOUT_CHOICES, default='text')

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f'{self.page.slug}: {self.title}'


class KnowledgeChunk(models.Model):
    SOURCE_TYPES = [
        ('destination', 'Điểm đến'),
        ('accommodation', 'Chỗ ở'),
        ('tour', 'Tour'),
        ('policy', 'Chính sách'),
        ('page', 'Trang nội dung'),
    ]

    source_type = models.CharField(max_length=24, choices=SOURCE_TYPES)
    source_id = models.PositiveBigIntegerField()
    title = models.CharField(max_length=240)
    content = models.TextField()
    url = models.CharField(max_length=300)
    metadata = models.JSONField(default=dict, blank=True)
    content_hash = models.CharField(max_length=64)
    embedding = models.JSONField(default=list)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['source_type', 'source_id']
        constraints = [
            models.UniqueConstraint(fields=['source_type', 'source_id'], name='unique_knowledge_chunk_source'),
        ]

    def __str__(self):
        return f'[{self.source_type}] {self.title}'


class UserCriteriaWeight(models.Model):
    """Trọng số cá nhân hóa dùng khi xếp hạng gợi ý của một người dùng."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='recommendation_weights')
    w1 = models.FloatField(default=0.4, validators=[MinValueValidator(0.1), MaxValueValidator(0.6)])
    w2 = models.FloatField(default=0.25, validators=[MinValueValidator(0.1), MaxValueValidator(0.6)])
    w3 = models.FloatField(default=0.2, validators=[MinValueValidator(0.1), MaxValueValidator(0.6)])
    w4 = models.FloatField(default=0.15, validators=[MinValueValidator(0.1), MaxValueValidator(0.6)])

    def clean(self):
        super().clean()
        if abs((self.w1 + self.w2 + self.w3 + self.w4) - 1.0) > 0.000001:
            raise ValidationError('Tổng bốn trọng số phải bằng 1.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Trọng số gợi ý của {self.user.username}'


class Destination(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    address = models.CharField(max_length=300, blank=True)
    reference_cost = models.PositiveIntegerField(default=0, help_text='Chi phí tham khảo cho chuyến 3 ngày 2 đêm, một người (VND).')
    category = models.CharField(max_length=50, choices=[
        ('biển', 'Biển'),
        ('núi', 'Núi'),
        ('thành phố', 'Thành phố'),
        ('ẩm thực', 'Ẩm thực'),
    ])
    latitude = models.FloatField(default=0.0)
    longitude = models.FloatField(default=0.0)
    vi_tri = models.PointField(srid=4326, spatial_index=True, null=True, blank=True)
    image_url = models.URLField(max_length=600, blank=True, default='')
    rating = models.FloatField(default=0.0)
    embedding_cache = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_embedding_fields = {
            'description': self.description,
            'category': self.category,
            'address': self.address,
        }

    def save(self, *args, **kwargs):
        update_fields = kwargs.get('update_fields')
        if self.pk and not self._state.adding:
            changed = {
                field for field in ('description', 'category', 'address')
                if getattr(self, field) != self._saved_embedding_fields.get(field)
            }
            self._embedding_changed_fields = changed if update_fields is None else changed & set(update_fields)
        else:
            self._embedding_changed_fields = {'description', 'category', 'address'}
        if self.latitude is not None and self.longitude is not None:
            self.vi_tri = Point(self.longitude, self.latitude, srid=4326)
            if update_fields is not None and ({'latitude', 'longitude'} & set(update_fields)):
                kwargs['update_fields'] = set(update_fields) | {'vi_tri'}
        super().save(*args, **kwargs)
        self._saved_embedding_fields = {
            'description': self.description,
            'category': self.category,
            'address': self.address,
        }

    def __str__(self):
        return self.name


@receiver(post_save, sender=Destination)
def destination_post_save_embedding(sender, instance, created, update_fields=None, **kwargs):
    """Queue a vector for new destinations or actual description/category changes."""
    if not created:
        changed_fields = set(update_fields or ())
        if update_fields is None:
            changed_fields = getattr(instance, '_embedding_changed_fields', set())
        if not ({'description', 'category', 'address'} & changed_fields):
            return
    try:
        from .tasks import compute_destination_embedding_task

        compute_destination_embedding_task.delay(instance.pk)
    except Exception:
        import logging

        logging.getLogger(__name__).exception('Could not enqueue destination embedding task for %s', instance.pk)


class RecommendationFeedback(models.Model):
    """Phản hồi của người dùng với một điểm đến đã xuất hiện trong gợi ý."""

    ACTION_CHOICES = [
        ('booked', 'Đã đặt'),
        ('viewed_detail', 'Đã xem chi tiết'),
        ('ignored', 'Bỏ qua'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendation_feedback')
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name='recommendation_feedback')
    # Giá trị có thể trống khi đơn được tạo từ luồng không đi qua danh sách gợi ý.
    preference_score = models.FloatField(null=True, blank=True)
    weather_score = models.FloatField(null=True, blank=True)
    budget_score = models.FloatField(null=True, blank=True)
    distance_score = models.FloatField(null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username}: {self.action} {self.destination.name}'


class Accommodation(models.Model):
    destination = models.ForeignKey(Destination, on_delete=models.SET_NULL, related_name='accommodations', null=True, blank=True)
    name = models.CharField(max_length=200)
    description = models.TextField(default='')
    category = models.CharField(max_length=50, choices=[
        ('hotel', 'Hotel'),
        ('homestay', 'Homestay'),
    ], default='hotel')
    latitude = models.FloatField(default=0.0)
    longitude = models.FloatField(default=0.0)
    vi_tri = models.PointField(srid=4326, spatial_index=True, null=True, blank=True)
    rating = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.latitude is not None and self.longitude is not None:
            self.vi_tri = Point(self.longitude, self.latitude, srid=4326)
            update_fields = kwargs.get('update_fields')
            if update_fields is not None and ({'latitude', 'longitude'} & set(update_fields)):
                kwargs['update_fields'] = set(update_fields) | {'vi_tri'}
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Amenity(models.Model):
    key = models.SlugField(max_length=80, unique=True)
    label = models.CharField(max_length=120)
    icon_name = models.CharField(max_length=40, choices=AMENITY_ICON_CHOICES, default='wifi')

    class Meta:
        ordering = ['label', 'key']

    def __str__(self):
        return self.label


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
    payment_provider = models.CharField(max_length=20, blank=True, default='')
    payment_order_ref = models.CharField(max_length=100, blank=True, default='')
    payment_transaction_id = models.CharField(max_length=64, blank=True, default='')
    payment_create_date = models.CharField(max_length=14, blank=True, default='')
    payment_pay_date = models.CharField(max_length=14, blank=True, default='')
    momo_trans_id = models.CharField(max_length=64, blank=True, default='')
    refund_status = models.CharField(
        max_length=12,
        choices=[('none', 'Chưa hoàn'), ('pending', 'Đang hoàn'), ('refunded', 'Đã hoàn'), ('failed', 'Hoàn thất bại')],
        default='none',
    )
    refunded_at = models.DateTimeField(null=True, blank=True)
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

        if self.status != 'cancelled' and self.check_in < timezone.localdate():
            raise ValidationError({'check_in': 'Ngày nhận phải lớn hơn hoặc bằng hôm nay.'})
        if self.status != 'cancelled' and self.check_out <= self.check_in:
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
        self.guest_phone = encrypt_phone(self.guest_phone)
        super().save(*args, **kwargs)

    def decrypt_guest_phone(self):
        return decrypt_phone(self.guest_phone)

    _encrypt_phone = staticmethod(encrypt_phone)

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


class Tour(models.Model):
    CATEGORY_CHOICES = [
        ('kham_pha', 'Khám phá thiên nhiên'),
        ('van_hoa', 'Văn hóa - Lịch sử'),
        ('nghi_duong', 'Nghỉ dưỡng'),
        ('mao_hiem', 'Mạo hiểm'),
        ('am_thuc', 'Ẩm thực'),
        ('ghep_doan', 'Tour ghép đoàn'),
        ('rieng', 'Tour riêng'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='kham_pha')
    duration_days = models.PositiveIntegerField()
    price_adult = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    price_child = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True)
    single_room_supplement = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    min_age = models.PositiveIntegerField(null=True, blank=True)
    included_services = models.JSONField(default=list, blank=True)
    excluded_services = models.JSONField(default=list, blank=True)
    cancellation_policy = models.TextField(blank=True, default='')
    price_per_person = models.DecimalField(max_digits=12, decimal_places=0, default=0, blank=True, null=True)
    cover_image_url = models.URLField(max_length=600, blank=True, default='')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.price_per_person:
            self.price_per_person = self.price_adult
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class TourStop(models.Model):
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name='stops')
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE)
    day_number = models.PositiveIntegerField()
    note = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['day_number']

    def __str__(self):
        return f'{self.tour.name} - Ngày {self.day_number}: {self.destination.name}'


class TourDeparture(models.Model):
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name='departures')
    departure_date = models.DateField()
    slots_total = models.PositiveIntegerField()
    is_cancelled = models.BooleanField(default=False)

    class Meta:
        ordering = ['departure_date']
        unique_together = ['tour', 'departure_date']

    def __str__(self):
        return f'{self.tour.name} - {self.departure_date} ({self.slots_total} chỗ)'


class TourBooking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tour_bookings')
    departure = models.ForeignKey(TourDeparture, on_delete=models.CASCADE, related_name='bookings')
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name='bookings', null=True, blank=True)
    departure_date = models.DateField(null=True, blank=True)
    num_guests = models.PositiveIntegerField(default=1)
    num_adults = models.PositiveIntegerField(default=1)
    num_children = models.PositiveIntegerField(default=0)
    is_single_room = models.BooleanField(default=False)
    guest_phone = models.TextField()
    total_price = models.DecimalField(max_digits=12, decimal_places=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    refund_amount = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    payment_provider = models.CharField(max_length=20, blank=True, default='')
    payment_order_ref = models.CharField(max_length=100, blank=True, default='')
    payment_transaction_id = models.CharField(max_length=64, blank=True, default='')
    payment_create_date = models.CharField(max_length=14, blank=True, default='')
    payment_pay_date = models.CharField(max_length=14, blank=True, default='')
    momo_trans_id = models.CharField(max_length=64, blank=True, default='')
    refund_status = models.CharField(
        max_length=12,
        choices=[('none', 'Chưa hoàn'), ('pending', 'Đang hoàn'), ('refunded', 'Đã hoàn'), ('failed', 'Hoàn thất bại')],
        default='none',
    )
    refunded_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def calculate_total_price(self):
        tour = self.departure.tour if self.departure_id else getattr(self, 'tour', None)
        if not tour:
            return self.total_price or 0
        price_adult = tour.price_adult or 0
        price_child = tour.price_child or 0
        supplement = tour.single_room_supplement if self.is_single_room else 0
        return (self.num_adults * price_adult) + (self.num_children * price_child) + supplement

    def clean(self):
        super().clean()
        if self.departure_id and self.status != 'cancelled':
            if self.departure.is_cancelled:
                raise ValidationError({'departure': 'Chuyến đi này đã bị hủy.'})
            if self.departure.departure_date and self.departure.departure_date < timezone.localdate():
                raise ValidationError({'departure': 'Ngày khởi hành không được ở quá khứ.'})
        if self.num_adults < 1:
            raise ValidationError({'num_adults': 'Số lượng người lớn tối thiểu là 1.'})
        if self.num_children < 0:
            raise ValidationError({'num_children': 'Số lượng trẻ em không thể âm.'})

    def save(self, *args, **kwargs):
        if self.departure_id:
            if not self.tour_id:
                self.tour = self.departure.tour
            self.departure_date = self.departure.departure_date
        self.num_guests = self.num_adults + self.num_children
        self.total_price = self.calculate_total_price()
        self.full_clean()
        if self.guest_phone:
            self.guest_phone = encrypt_phone(self.guest_phone)
        super().save(*args, **kwargs)

    def decrypt_guest_phone(self):
        return decrypt_phone(self.guest_phone)

    def cancel_booking(self, refund_amount=0):
        self.status = 'cancelled'
        self.refund_amount = refund_amount
        self.save(update_fields=['status', 'refund_amount'])
        return self

    def __str__(self):
        return f'{self.user.username} - {self.departure}'


class AccommodationReview(models.Model):
    accommodation = models.ForeignKey(Accommodation, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    booking = models.OneToOneField('Booking', on_delete=models.SET_NULL, null=True, blank=True, related_name='review')
    rating = models.PositiveSmallIntegerField(default=5)
    comment = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} review for {self.accommodation.name}'


class DemoAccommodationRatingSnapshot(models.Model):
    """Preserves an accommodation's pre-demo rating so demo removal can restore it."""
    accommodation = models.OneToOneField(Accommodation, on_delete=models.CASCADE, related_name='demo_rating_snapshot')
    rating = models.FloatField(default=0)


class ChatMessage(models.Model):
    ATTACHMENT_TYPES = [
        ('none', 'Không có'),
        ('image', 'Ảnh'),
        ('pdf', 'PDF'),
    ]
    conversation_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chat_conversations',
        null=True,
        blank=True,
    )
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages', null=True, blank=True)
    content = models.TextField()
    attachment = models.FileField(upload_to='chat_attachments/%Y/%m/', null=True, blank=True)
    attachment_type = models.CharField(max_length=10, choices=ATTACHMENT_TYPES, default='none')
    is_from_admin = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        recipient = self.receiver.username if self.receiver_id else f'cuộc trò chuyện {self.conversation_user_id}'
        return f'{self.sender.username} -> {recipient}: {self.content[:40]}'


class TravelPost(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='travel_posts')
    title = models.CharField(max_length=200)
    content = models.TextField()
    destination = models.ForeignKey(Destination, on_delete=models.SET_NULL, null=True, blank=True, related_name='travel_posts')
    images = models.JSONField(default=list, blank=True)
    likes_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} - {self.user.username}'


class TravelPostLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_likes')
    post = models.ForeignKey(TravelPost, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'post']

    def __str__(self):
        return f'{self.user.username} thích bài {self.post_id}'


class RecommendationLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='recommendation_logs')
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name='recommendation_logs')
    score = models.FloatField()
    search_id = models.UUIDField(default=uuid.uuid4, null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        username = self.user.username if self.user else 'Khách'
        return f'{username} -> {self.destination.name} ({self.score:.2f})'
