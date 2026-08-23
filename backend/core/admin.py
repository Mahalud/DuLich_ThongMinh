from django.contrib import admin

from .models import Accommodation, AccommodationReview, Booking, Destination, RoomType, SearchHistory, UserProfile

admin.site.register(UserProfile)
admin.site.register(SearchHistory)
admin.site.register(Destination)
admin.site.register(Accommodation)
admin.site.register(RoomType)
admin.site.register(Booking)
admin.site.register(AccommodationReview)
