from django.urls import path
from . import views

app_name = 'offers'

urlpatterns = [
    path('listing/<int:pk>/make/', views.make_offer, name='make'),
    path('<int:pk>/', views.offer_detail, name='detail'),
    path('mine/', views.my_offers, name='my_offers'),
    path('received/', views.received_offers, name='received'),
]
