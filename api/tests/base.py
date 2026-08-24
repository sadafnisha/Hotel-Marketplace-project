from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from listings.models import HotelListing

User = get_user_model()


class ApiTestBase(APITestCase):
    """Common fixtures reused across API test modules."""

    def setUp(self):
        self.owner = User.objects.create_user(
            username='owner1', email='owner1@test.com', password='Password123',
            role=User.Role.OWNER,
        )
        self.other_owner = User.objects.create_user(
            username='owner2', email='owner2@test.com', password='Password123',
            role=User.Role.OWNER,
        )
        self.buyer = User.objects.create_user(
            username='buyer1', email='buyer1@test.com', password='Password123',
            role=User.Role.BUYER,
        )
        self.other_buyer = User.objects.create_user(
            username='buyer2', email='buyer2@test.com', password='Password123',
            role=User.Role.BUYER,
        )
        self.admin = User.objects.create_user(
            username='admin1', email='admin1@test.com', password='Password123',
            role=User.Role.ADMIN, is_staff=True,
        )

        self.published_listing = HotelListing.objects.create(
            owner=self.owner, title='Published Hotel', description='A nice hotel.',
            property_type=HotelListing.PropertyType.BUSINESS_HOTEL,
            address='1 Main Rd', city='Lucknow', state='UP', country='India',
            rooms=40, asking_amount=Decimal('5000000'),
            status=HotelListing.Status.PUBLISHED,
        )
        self.draft_listing = HotelListing.objects.create(
            owner=self.owner, title='Draft Hotel', description='Not yet live.',
            property_type=HotelListing.PropertyType.BOUTIQUE,
            address='2 Main Rd', city='Lucknow', state='UP', country='India',
            rooms=20, asking_amount=Decimal('2000000'),
            status=HotelListing.Status.DRAFT,
        )
        self.closed_listing = HotelListing.objects.create(
            owner=self.owner, title='Closed Hotel', description='No longer available.',
            property_type=HotelListing.PropertyType.RESORT,
            address='3 Main Rd', city='Jaipur', state='Rajasthan', country='India',
            rooms=60, asking_amount=Decimal('9000000'),
            status=HotelListing.Status.CLOSED,
        )

    def auth_as(self, user):
        self.client.force_authenticate(user=user)

    def logout(self):
        self.client.force_authenticate(user=None)
