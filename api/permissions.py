"""
Custom permission classes for the REST API.

These deliberately reuse the same role helpers already defined on
``accounts.models.User`` (``is_owner``, ``is_buyer``, ``is_platform_admin``)
so the business rules match the server-rendered views exactly -- there is
no separate/duplicated notion of "who can do what".
"""
from rest_framework import permissions


class IsOwnerRole(permissions.BasePermission):
    """Allows access only to authenticated users with the Owner role."""

    message = 'Only hotel owners can perform this action.'

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_owner
        )


class IsBuyerRole(permissions.BasePermission):
    """Allows access only to authenticated users with the Buyer role."""

    message = 'Only buyers can perform this action.'

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_buyer
        )


class IsAdminRole(permissions.BasePermission):
    """Allows access only to platform admins (role=admin, staff or superuser)."""

    message = 'Admin privileges are required for this action.'

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_platform_admin
        )


class IsListingOwnerOrReadOnly(permissions.BasePermission):
    """
    Anyone (subject to queryset-level visibility rules) may read a listing.
    Only the owning Owner (or an admin) may update/delete it.
    """

    message = 'You can only edit or delete your own listings.'

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (obj.owner_id == user.id or user.is_platform_admin)
        )


class IsOfferParticipantOrAdmin(permissions.BasePermission):
    """Only the buyer, the owner involved in the offer, or an admin may view/act on it."""

    message = 'Not authorized to access this offer.'

    def has_object_permission(self, request, view, obj):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (user.id in (obj.buyer_id, obj.owner_id) or user.is_platform_admin)
        )


class IsConversationParticipantOrAdmin(permissions.BasePermission):
    """Only the buyer and owner of a conversation (or an admin) may access it."""

    message = 'Not authorized to access this conversation.'

    def has_object_permission(self, request, view, obj):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (user.id in (obj.buyer_id, obj.owner_id) or user.is_platform_admin)
        )
