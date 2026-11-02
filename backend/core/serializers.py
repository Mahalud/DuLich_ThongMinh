from django.utils import timezone
from rest_framework import serializers

from .models import (
    AMENITY_ICON_CHOICES,
    Amenity,
    Accommodation,
    AccommodationReview,
    Booking,
    ChatMessage,
    Destination,
    RoomType,
    SearchHistory,
    SitePage,
    SitePageSection,
    Tour,
    TourBooking,
    TourDeparture,
    TourStop,
    TravelPost,
    TravelPostLike,
    UserProfile,
)
from .cancellations import cancellation_refund_preview


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['id', 'travel_preferences', 'budget_estimate', 'weather_preference', 'free_text', 'created_at', 'updated_at']


class SitePageSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SitePageSection
        fields = ['id', 'order', 'title', 'content', 'image_url', 'layout']
        read_only_fields = ['id']


class SitePageSerializer(serializers.ModelSerializer):
    sections = SitePageSectionSerializer(many=True, read_only=True)

    class Meta:
        model = SitePage
        fields = ['id', 'slug', 'title', 'cover_image_url', 'intro', 'updated_at', 'sections']
        read_only_fields = ['id', 'slug', 'updated_at', 'sections']


class DestinationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Destination
        fields = [
            'id',
            'name',
            'description',
            'address',
            'category',
            'latitude',
            'longitude',
            'image_url',
            'rating',
            'reference_cost',
        ]


class AmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Amenity
        fields = ['id', 'key', 'label', 'icon_name']

    def validate_icon_name(self, value):
        if value not in {key for key, _ in AMENITY_ICON_CHOICES}:
            raise serializers.ValidationError('Biểu tượng tiện ích không hợp lệ.')
        return value

    def validate_key(self, value):
        if self.instance and value != self.instance.key:
            raise serializers.ValidationError('Không thể đổi khóa sau khi tiện ích đã được tạo.')
        return value


class RoomTypeSerializer(serializers.ModelSerializer):
    accommodation_name = serializers.CharField(source='accommodation.name', read_only=True)
    base_price = serializers.IntegerField(min_value=0)

    class Meta:
        model = RoomType
        fields = [
            'id',
            'accommodation',
            'accommodation_name',
            'name',
            'base_price',
            'stock',
            'amenities',
        ]
        extra_kwargs = {
            'accommodation': {'required': False},
            'stock': {'min_value': 1},
        }

    def validate_amenities(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError('amenities phải là một danh sách các key tiện ích.')
        valid_keys = set(Amenity.objects.values_list('key', flat=True))
        unknown_keys = [key for key in value if key not in valid_keys]
        if unknown_keys:
            raise serializers.ValidationError(
                f'Key tiện ích không hợp lệ: {", ".join(map(str, unknown_keys))}. '
                f'Key hợp lệ gồm: {", ".join(valid_keys)}.'
            )
        return value


class AccommodationSerializer(serializers.ModelSerializer):
    room_types = RoomTypeSerializer(many=True, read_only=True)
    distance_km = serializers.SerializerMethodField()

    class Meta:
        model = Accommodation
        fields = ['id', 'destination', 'name', 'description', 'category', 'latitude', 'longitude', 'rating', 'distance_km', 'room_types']

    def get_distance_km(self, obj):
        distance = getattr(obj, 'distance_m', None)
        return round(distance.m / 1000, 1) if distance is not None else None


class BookingSerializer(serializers.ModelSerializer):
    decrypted_phone = serializers.SerializerMethodField()
    room_type_name = serializers.CharField(source='room_type.name', read_only=True)
    accommodation_name = serializers.CharField(source='room_type.accommodation.name', read_only=True)
    accommodation_id = serializers.IntegerField(source='room_type.accommodation_id', read_only=True)
    nights = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    refund_preview = serializers.SerializerMethodField()
    payment_simulated = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            'id',
            'user',
            'room_type',
            'room_type_name',
            'accommodation_name',
            'accommodation_id',
            'check_in',
            'check_out',
            'nights',
            'total_price',
            'guest_phone',
            'decrypted_phone',
            'status',
            'refund_amount',
            'refund_status',
            'refund_preview',
            'payment_simulated',
            'refunded_at',
            'created_at',
        ]
        read_only_fields = ['id', 'user', 'decrypted_phone', 'created_at', 'status', 'refund_amount', 'refund_status', 'refunded_at']

    def get_decrypted_phone(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return ''
        if not (request.user.is_staff or request.user.is_superuser or request.user.pk == obj.user_id):
            return ''
        return obj.decrypt_guest_phone()

    def get_payment_simulated(self, obj):
        return obj.payment_provider == 'simulated' or str(obj.momo_trans_id or '').startswith('SIM-')

    def get_nights(self, obj):
        return max(0, (obj.check_out - obj.check_in).days)

    def get_total_price(self, obj):
        return int(obj.room_type.base_price * self.get_nights(obj))

    def get_refund_preview(self, obj):
        return cancellation_refund_preview(obj, is_tour=False)


class TourStopSerializer(serializers.ModelSerializer):
    destination = DestinationSerializer(read_only=True)
    destination_id = serializers.PrimaryKeyRelatedField(source='destination', queryset=Destination.objects.all(), write_only=True)

    class Meta:
        model = TourStop
        fields = ['id', 'destination', 'destination_id', 'day_number', 'note']


class TourDepartureSerializer(serializers.ModelSerializer):
    slots_booked = serializers.SerializerMethodField()
    slots_available = serializers.SerializerMethodField()

    class Meta:
        model = TourDeparture
        fields = ['id', 'tour', 'departure_date', 'slots_total', 'is_cancelled', 'slots_booked', 'slots_available']

    def get_slots_booked(self, obj):
        return sum(
            (b.num_adults + b.num_children)
            for b in obj.bookings.filter(status__in=['pending', 'confirmed'])
        )

    def get_slots_available(self, obj):
        booked = self.get_slots_booked(obj)
        return max(0, obj.slots_total - booked)


class TourSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tour
        fields = [
            'id',
            'name',
            'description',
            'category',
            'duration_days',
            'price_adult',
            'price_child',
            'single_room_supplement',
            'min_age',
            'included_services',
            'excluded_services',
            'cancellation_policy',
            'price_per_person',
            'cover_image_url',
            'is_active',
            'created_at',
        ]


class TourDetailSerializer(TourSerializer):
    stops = TourStopSerializer(many=True, read_only=True)
    departures = serializers.SerializerMethodField()

    def get_departures(self, obj):
        departures = obj.departures.filter(
            departure_date__gte=timezone.localdate(),
            is_cancelled=False,
        ).order_by('departure_date')
        results = []
        for item in departures:
            booked = sum(
                (b.num_adults + b.num_children)
                for b in item.bookings.filter(status__in=['pending', 'confirmed'])
            )
            results.append({
                'id': item.id,
                'departure_date': item.departure_date,
                'slots_total': item.slots_total,
                'slots_booked': booked,
                'slots_available': max(0, item.slots_total - booked),
            })
        return results

    class Meta(TourSerializer.Meta):
        fields = TourSerializer.Meta.fields + ['stops', 'departures']


class TourBookingSerializer(serializers.ModelSerializer):
    decrypted_phone = serializers.SerializerMethodField(read_only=True)
    total_price = serializers.DecimalField(max_digits=12, decimal_places=0, read_only=True)
    tour_name = serializers.CharField(source='departure.tour.name', read_only=True)
    tour_id = serializers.IntegerField(source='departure.tour.id', read_only=True)
    departure_date = serializers.DateField(source='departure.departure_date', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    refund_preview = serializers.SerializerMethodField()
    payment_simulated = serializers.SerializerMethodField()

    class Meta:
        model = TourBooking
        fields = [
            'id',
            'user',
            'username',
            'departure',
            'tour_id',
            'tour_name',
            'departure_date',
            'num_adults',
            'num_children',
            'is_single_room',
            'total_price',
            'guest_phone',
            'decrypted_phone',
            'status',
            'refund_amount',
            'refund_status',
            'refund_preview',
            'payment_simulated',
            'refunded_at',
            'created_at',
        ]
        read_only_fields = ['id', 'user', 'total_price', 'decrypted_phone', 'status', 'refund_amount', 'refund_status', 'refunded_at', 'created_at']

    def get_decrypted_phone(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return ''
        if not (request.user.is_staff or request.user.is_superuser or request.user.pk == obj.user_id):
            return ''
        return obj.decrypt_guest_phone()

    def get_payment_simulated(self, obj):
        return obj.payment_provider == 'simulated' or str(obj.momo_trans_id or '').startswith('SIM-')

    def get_refund_preview(self, obj):
        return cancellation_refund_preview(obj, is_tour=True)


class AdminBookingSerializer(BookingSerializer):
    class Meta(BookingSerializer.Meta):
        fields = [
            'id',
            'user',
            'room_type',
            'room_type_name',
            'check_in',
            'check_out',
            'decrypted_phone',
            'status',
            'refund_amount',
            'refund_status',
            'refunded_at',
            'created_at',
        ]


class AccommodationReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    user_is_demo = serializers.SerializerMethodField()

    def get_user_name(self, obj):
        return obj.user.get_full_name() or obj.user.username

    def get_user_is_demo(self, obj):
        return bool(getattr(getattr(obj.user, 'profile', None), 'is_demo', False))

    class Meta:
        model = AccommodationReview
        fields = ['id', 'booking', 'accommodation', 'user', 'user_name', 'user_is_demo', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'accommodation', 'user', 'user_name', 'created_at']


class SearchHistorySerializer(serializers.ModelSerializer):
    destination_name = serializers.CharField(source='destination.name', read_only=True, allow_null=True)

    class Meta:
        model = SearchHistory
        fields = ['id', 'user', 'query', 'preferences', 'budget_estimate', 'weather_preference', 'latitude', 'longitude', 'travel_date', 'top_n', 'destination', 'destination_name', 'created_at']
        read_only_fields = ['id', 'user', 'destination_name', 'created_at']


class ChatMessageSerializer(serializers.ModelSerializer):
    attachment_url = serializers.SerializerMethodField()
    sender_name = serializers.CharField(source='sender.username', read_only=True)

    class Meta:
        model = ChatMessage
        fields = ['id', 'conversation_user', 'sender', 'sender_name', 'is_from_admin', 'content', 'attachment_url', 'attachment_type', 'created_at', 'is_read']
        read_only_fields = fields

    def get_attachment_url(self, obj):
        if not obj.attachment:
            return ''
        request = self.context.get('request')
        return request.build_absolute_uri(obj.attachment.url) if request else obj.attachment.url


class TravelPostSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    user_is_demo = serializers.SerializerMethodField()
    destination_name = serializers.CharField(source='destination.name', read_only=True, default=None)
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = TravelPost
        fields = [
            'id',
            'user',
            'user_name',
            'user_is_demo',
            'title',
            'content',
            'destination',
            'destination_name',
            'images',
            'likes_count',
            'is_liked',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'user', 'user_name', 'destination_name', 'likes_count', 'is_liked', 'created_at', 'updated_at']

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return TravelPostLike.objects.filter(user=request.user, post=obj).exists()
        return False

    def get_user_name(self, obj):
        return obj.user.get_full_name() or obj.user.username

    def get_user_is_demo(self, obj):
        return bool(getattr(getattr(obj.user, 'profile', None), 'is_demo', False))

    def validate_images(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError('images phải là một danh sách URL.')
        if len(value) > 5:
            raise serializers.ValidationError('Tối đa 5 ảnh mỗi bài viết.')
        return value
