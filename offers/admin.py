from django.contrib import admin
from .models import Offer, OfferHistory


class OfferHistoryInline(admin.TabularInline):
    model = OfferHistory
    extra = 0
    readonly_fields = ('actor', 'action', 'amount', 'message', 'timestamp')


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ('id', 'listing', 'buyer', 'owner', 'amount', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('listing__title', 'buyer__username', 'owner__username')
    inlines = [OfferHistoryInline]
