from django.contrib import admin
from .models import HotelListing, HotelImage, Favourite


class HotelImageInline(admin.TabularInline):
    model = HotelImage
    extra = 1


@admin.register(HotelListing)
class HotelListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'reference_number', 'owner', 'city', 'status', 'asking_amount', 'created_at')
    list_filter = ('status', 'property_type', 'city')
    search_fields = ('title', 'reference_number', 'city', 'owner__username')
    inlines = [HotelImageInline]
    actions = ['approve_listings', 'reject_listings']

    @admin.action(description='Approve & publish selected listings')
    def approve_listings(self, request, queryset):
        from django.utils import timezone
        queryset.update(status=HotelListing.Status.PUBLISHED, published_at=timezone.now())

    @admin.action(description='Reject selected listings')
    def reject_listings(self, request, queryset):
        queryset.update(status=HotelListing.Status.REJECTED)


@admin.register(Favourite)
class FavouriteAdmin(admin.ModelAdmin):
    list_display = ('buyer', 'listing', 'created_at')
