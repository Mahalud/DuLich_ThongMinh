from rest_framework import serializers

from .models import Accommodation, AccommodationReview, Booking, ChatMessage, Destination, RoomType, SearchHistory, UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['id', 'travel_preferences', 'budget_estimate', 'free_text', 'created_at', 'updated_at']


class DestinationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Destination
        fields = [
            'id',
            'name',
            'description',
            'category',
            'latitude',
            'longitude',
            'image_url',
            'rating',
        ]


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


class AccommodationSerializer(serializers.ModelSerializer):
    room_types = RoomTypeSerializer(many=True, read_only=True)

    class Meta:
        model = Accommodation
        fields = ['id', 'name', 'description', 'category', 'latitude', 'longitude', 'rating', 'room_types']


class BookingSerializer(serializers.ModelSerializer):
    decrypted_phone = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            'id',
            'user',
            'room_type',
            'check_in',
            'check_out',
            'guest_phone',
            'decrypted_phone',
            'status',
            'refund_amount',
            'created_at',
        ]
        read_only_fields = ['id', 'decrypted_phone', 'created_at', 'status', 'refund_amount']

    def get_decrypted_phone(self, obj):
        return obj.decrypt_guest_phone()


class AccommodationReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = AccommodationReview
        fields = ['id', 'accommodation', 'user', 'user_name', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'created_at']


class SearchHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchHistory
        fields = ['id', 'user', 'query', 'created_at']
        read_only_fields = ['id', 'created_at']


class ChatMessageSerializer(serializers.ModelSerializer):
    attachment_url = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = ['id', 'sender', 'receiver', 'content', 'attachment_url', 'attachment_type', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_attachment_url(self, obj):
        if not obj.attachment:
            return ''
        request = self.context.get('request')
        return request.build_absolute_uri(obj.attachment.url) if request else obj.attachment.url
