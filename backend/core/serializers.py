from rest_framework import serializers

from .models import Accommodation, Booking, Destination, RoomType, SearchHistory, UserProfile


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
            'created_at',
        ]
        read_only_fields = ['id', 'decrypted_phone', 'created_at', 'status']

    def get_decrypted_phone(self, obj):
        return obj.decrypt_guest_phone()


class SearchHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchHistory
        fields = ['id', 'user', 'query', 'created_at']
        read_only_fields = ['id', 'created_at']
