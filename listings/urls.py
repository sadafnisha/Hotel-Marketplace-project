from django.urls import path
from . import views

app_name = 'listings'

urlpatterns = [
    path('', views.marketplace, name='marketplace'),
    path('mine/', views.my_listings, name='my_listings'),
    path('saved/', views.saved_listings, name='saved'),
    path('create/', views.create_listing, name='create'),
    path('<int:pk>/', views.listing_detail, name='detail'),
    path('<int:pk>/edit/', views.edit_listing, name='edit'),
    path('<int:pk>/status/<str:new_status>/', views.update_listing_status, name='update_status'),
    path('<int:pk>/favourite/', views.toggle_favourite, name='toggle_favourite'),
]
