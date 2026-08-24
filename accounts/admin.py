from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, OwnerProfile, BuyerProfile


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'status', 'is_staff', 'created_at')
    list_filter = ('role', 'status', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('Marketplace info', {'fields': ('role', 'phone', 'status')}),
    )


@admin.register(OwnerProfile)
class OwnerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'business_name', 'is_verified', 'created_at')
    search_fields = ('business_name', 'user__username')


@admin.register(BuyerProfile)
class BuyerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'company_name', 'created_at')
    search_fields = ('company_name', 'user__username')
