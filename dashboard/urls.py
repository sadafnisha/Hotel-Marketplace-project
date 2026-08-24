from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.redirect_dashboard, name='redirect'),
    path('owner/', views.owner_dashboard, name='owner'),
    path('buyer/', views.buyer_dashboard, name='buyer'),
    path('admin/', views.admin_dashboard, name='admin'),
    path('admin/listings/', views.admin_listings, name='admin_listings'),
    path('admin/listings/<int:pk>/<str:action>/', views.admin_moderate_listing, name='admin_moderate_listing'),
    path('admin/users/', views.admin_users, name='admin_users'),
    path('admin/users/<int:pk>/toggle/', views.admin_toggle_user_status, name='admin_toggle_user'),
]
