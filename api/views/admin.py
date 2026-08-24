"""
Admin-only API endpoints, mirroring dashboard/views.py's admin_* views.
Every view here is gated behind `IsAdminRole` (role=admin, staff or superuser).
"""
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from listings.models import HotelListing
from api.permissions import IsAdminRole
from api.serializers import UserSerializer, HotelListingDetailSerializer

User = get_user_model()


class AdminUserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    /api/admin/users/                GET - list all users (optional ?role= filter)
    /api/admin/users/{id}/           GET - user detail
    /api/admin/users/{id}/toggle-status/  POST - suspend/reactivate a user
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]

    def get_queryset(self):
        qs = User.objects.exclude(is_superuser=True).order_by('-date_joined')
        role = self.request.query_params.get('role')
        if role:
            qs = qs.filter(role=role)
        return qs

    @action(detail=True, methods=['post'], url_path='toggle-status')
    def toggle_status(self, request, pk=None):
        user = self.get_object()
        user.status = User.Status.SUSPENDED if user.status == User.Status.ACTIVE else User.Status.ACTIVE
        user.is_active = user.status == User.Status.ACTIVE
        user.save()
        return Response(UserSerializer(user).data)


class AdminListingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    /api/admin/listings/                GET - list all listings, any status (optional ?status=)
    /api/admin/listings/{id}/           GET - listing detail
    /api/admin/listings/{id}/moderate/  POST {"action": "approve"|"reject"|"suspend"}
    """
    serializer_class = HotelListingDetailSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]

    def get_queryset(self):
        qs = HotelListing.objects.select_related('owner').order_by('-created_at')
        listing_status = self.request.query_params.get('status')
        if listing_status:
            qs = qs.filter(status=listing_status)
        return qs

    @action(detail=True, methods=['post'])
    def moderate(self, request, pk=None):
        listing = self.get_object()
        mod_action = request.data.get('action')
        if mod_action == 'approve':
            listing.status = HotelListing.Status.PUBLISHED
            listing.published_at = timezone.now()
        elif mod_action == 'reject':
            listing.status = HotelListing.Status.REJECTED
        elif mod_action == 'suspend':
            listing.status = HotelListing.Status.CLOSED
        else:
            return Response({'detail': 'Unknown action.'}, status=status.HTTP_400_BAD_REQUEST)
        listing.save()
        return Response(HotelListingDetailSerializer(listing).data)
