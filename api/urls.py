"""
REST API URL configuration.

Mounted at /api/ from hotel_marketplace/urls.py. This is purely additive --
none of the existing server-rendered routes (accounts/, dashboard/, offers/,
messages/, listings root) are changed or removed.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.views.auth import RegisterView, LoginView, LogoutView, MeView
from api.views.listings import HotelListingViewSet, FavouriteViewSet
from api.views.offers import OfferViewSet
from api.views.chat import ConversationViewSet
from api.views.admin import AdminUserViewSet, AdminListingViewSet

router = DefaultRouter()
router.register('listings', HotelListingViewSet, basename='listing')
router.register('favourites', FavouriteViewSet, basename='favourite')
router.register('offers', OfferViewSet, basename='offer')
router.register('conversations', ConversationViewSet, basename='conversation')
router.register('admin/users', AdminUserViewSet, basename='admin-user')
router.register('admin/listings', AdminListingViewSet, basename='admin-listing')

app_name = 'api'

urlpatterns = [
    # Authentication
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),

    # Current user
    path('users/me/', MeView.as_view(), name='me'),

    # Browsable-API login/logout (session auth), handy for manual testing in a browser
    path('auth-browsable/', include('rest_framework.urls')),

    # Listings, favourites, offers, conversations, admin (router-based)
    path('', include(router.urls)),
]
