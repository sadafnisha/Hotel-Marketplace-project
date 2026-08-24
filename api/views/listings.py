"""
Hotel Listings & Favourites API.

Business rules enforced here mirror listings/views.py exactly:
  * Only authenticated Owners can create listings (status starts as Draft).
  * Owners can edit/delete only their own listings.
  * Only Published listings are publicly visible (list + retrieve for
    everyone else); the owner and platform admins may still see their own
    non-published listings.
  * Status transitions (publish/unpublish/close) are limited to the owner.
"""
from django.db.models import Q
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from listings.models import HotelListing, Favourite
from api.permissions import IsOwnerRole, IsListingOwnerOrReadOnly
from api.serializers import (
    HotelListingListSerializer,
    HotelListingDetailSerializer,
    HotelListingWriteSerializer,
    FavouriteSerializer,
)


class HotelListingViewSet(viewsets.ModelViewSet):
    """
    /api/listings/            GET (list, public+filters), POST (Owner only -> create draft)
    /api/listings/{id}/       GET (retrieve), PUT/PATCH (owner), DELETE (owner/admin)
    /api/listings/{id}/publish/    POST (owner) - submit for approval (-> Pending)
    /api/listings/{id}/unpublish/  POST (owner) - revert to Draft
    /api/listings/{id}/close/      POST (owner) - close listing (stops new offers)
    /api/listings/mine/            GET (owner) - all of the caller's own listings, any status
    """
    lookup_field = 'pk'
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsListingOwnerOrReadOnly]

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.IsAuthenticated(), IsOwnerRole()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'list':
            return HotelListingListSerializer
        if self.action in ('create', 'update', 'partial_update'):
            return HotelListingWriteSerializer
        return HotelListingDetailSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        user = self.request.user
        if user.is_authenticated and getattr(user, 'is_buyer', False):
            context['favourite_ids'] = set(
                Favourite.objects.filter(buyer=user).values_list('listing_id', flat=True)
            )
        return context

    def get_queryset(self):
        user = self.request.user
        qs = HotelListing.objects.select_related('owner').prefetch_related('images')

        if self.action == 'mine':
            if not (user.is_authenticated and user.is_owner):
                return HotelListing.objects.none()
            return qs.filter(owner=user)

        if user.is_authenticated and user.is_platform_admin:
            visible = qs  # admins can see everything (moderation happens in the admin API)
        elif user.is_authenticated and user.is_owner:
            # Owners browsing the marketplace see published listings + their own of any status.
            visible = qs.filter(Q(status=HotelListing.Status.PUBLISHED) | Q(owner=user))
        else:
            visible = qs.filter(status=HotelListing.Status.PUBLISHED)

        if self.action == 'list':
            visible = self._apply_search_filters(visible)
        return visible

    def _apply_search_filters(self, qs):
        """Mirrors listings.forms.ListingSearchForm / listings.views.marketplace filtering."""
        params = self.request.query_params
        q = params.get('q')
        city = params.get('city')
        property_type = params.get('property_type')
        min_price = params.get('min_price')
        max_price = params.get('max_price')
        min_rooms = params.get('min_rooms')
        sort = params.get('sort', 'newest')

        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(city__icontains=q) | Q(address__icontains=q))
        if city:
            qs = qs.filter(city__icontains=city)
        if property_type:
            qs = qs.filter(property_type=property_type)
        if min_price:
            qs = qs.filter(asking_amount__gte=min_price)
        if max_price:
            qs = qs.filter(asking_amount__lte=max_price)
        if min_rooms:
            qs = qs.filter(rooms__gte=min_rooms)

        sort_map = {
            'newest': '-created_at',
            'price_low': 'asking_amount',
            'price_high': '-asking_amount',
            'rooms': '-rooms',
        }
        return qs.order_by(sort_map.get(sort, '-created_at'))

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        is_owner = request.user.is_authenticated and instance.owner_id == request.user.id
        is_admin = request.user.is_authenticated and request.user.is_platform_admin
        if instance.status != HotelListing.Status.PUBLISHED and not is_owner and not is_admin:
            return Response(
                {'detail': 'This listing is not currently available.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def perform_create(self, serializer):
        # New listings always start as Draft, exactly like listings.views.create_listing.
        serializer.save(owner=self.request.user, status=HotelListing.Status.DRAFT)

    def perform_update(self, serializer):
        listing = self.get_object()
        if listing.owner_id != self.request.user.id and not self.request.user.is_platform_admin:
            raise PermissionDenied('You can only edit your own listings.')
        serializer.save()

    def perform_destroy(self, instance):
        if instance.owner_id != self.request.user.id and not self.request.user.is_platform_admin:
            raise PermissionDenied('You can only delete your own listings.')
        instance.delete()

    @action(detail=False, methods=['get'])
    def mine(self, request):
        page = self.paginate_queryset(self.get_queryset())
        serializer = HotelListingListSerializer(page or self.get_queryset(), many=True, context=self.get_serializer_context())
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    def _transition(self, request, pk, new_status, set_published_at=False):
        listing = self.get_object()
        if listing.owner_id != request.user.id:
            raise PermissionDenied('Not authorized.')
        listing.status = new_status
        if set_published_at:
            listing.published_at = timezone.now()
        listing.save()
        return Response(HotelListingDetailSerializer(listing, context=self.get_serializer_context()).data)

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """Submit a Draft listing for admin approval (-> Pending)."""
        return self._transition(request, pk, HotelListing.Status.PENDING, set_published_at=False)

    @action(detail=True, methods=['post'])
    def unpublish(self, request, pk=None):
        """Revert a listing back to Draft."""
        return self._transition(request, pk, HotelListing.Status.DRAFT)

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """Close a listing; closed listings can no longer accept new offers."""
        return self._transition(request, pk, HotelListing.Status.CLOSED)


class FavouriteViewSet(viewsets.ModelViewSet):
    """
    /api/favourites/         GET (buyer's own saved listings), POST {"listing": <id>} to save
    /api/favourites/{id}/    DELETE to remove
    Only Buyers have favourites, mirroring listings.views.toggle_favourite / saved_listings.
    """
    serializer_class = FavouriteSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'delete', 'head', 'options']

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated or not user.is_buyer:
            return Favourite.objects.none()
        return Favourite.objects.filter(buyer=user).select_related('listing')

    def create(self, request, *args, **kwargs):
        if not request.user.is_buyer:
            return Response(
                {'detail': 'Only buyers can save listings.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().create(request, *args, **kwargs)

    def perform_destroy(self, instance):
        if instance.buyer_id != self.request.user.id:
            raise PermissionDenied('You can only remove your own saved listings.')
        instance.delete()
