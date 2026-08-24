from rest_framework import status

from listings.models import HotelListing
from .base import ApiTestBase


class ListingVisibilityTests(ApiTestBase):
    def test_anonymous_sees_only_published_listings(self):
        resp = self.client.get('/api/listings/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        titles = [item['title'] for item in resp.data['results']]
        self.assertIn('Published Hotel', titles)
        self.assertNotIn('Draft Hotel', titles)

    def test_anonymous_cannot_retrieve_draft_listing(self):
        resp = self.client.get(f'/api/listings/{self.draft_listing.pk}/')
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_owner_can_retrieve_own_draft_listing(self):
        self.auth_as(self.owner)
        resp = self.client.get(f'/api/listings/{self.draft_listing.pk}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_other_owner_cannot_retrieve_someone_elses_draft(self):
        self.auth_as(self.other_owner)
        resp = self.client.get(f'/api/listings/{self.draft_listing.pk}/')
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_can_retrieve_any_listing(self):
        self.auth_as(self.admin)
        resp = self.client.get(f'/api/listings/{self.draft_listing.pk}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


class ListingCreateTests(ApiTestBase):
    valid_payload = {
        'title': 'Brand New Hotel', 'description': 'Fresh listing.',
        'property_type': 'business_hotel',
        'address': '9 New Rd', 'city': 'Pune', 'state': 'MH', 'country': 'India',
        'rooms': 30, 'asking_amount': '3000000',
    }

    def test_anonymous_cannot_create_listing(self):
        resp = self.client.post('/api/listings/', self.valid_payload)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_buyer_cannot_create_listing(self):
        self.auth_as(self.buyer)
        resp = self.client.post('/api/listings/', self.valid_payload)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_can_create_listing_as_draft(self):
        self.auth_as(self.owner)
        resp = self.client.post('/api/listings/', self.valid_payload)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        listing = HotelListing.objects.get(title='Brand New Hotel')
        self.assertEqual(listing.owner, self.owner)
        self.assertEqual(listing.status, HotelListing.Status.DRAFT)

    def test_invalid_asking_amount_rejected(self):
        self.auth_as(self.owner)
        payload = dict(self.valid_payload, asking_amount='-100')
        resp = self.client.post('/api/listings/', payload)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class ListingEditDeleteTests(ApiTestBase):
    def test_owner_can_edit_own_listing(self):
        self.auth_as(self.owner)
        resp = self.client.patch(f'/api/listings/{self.draft_listing.pk}/', {'title': 'Updated Title'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.draft_listing.refresh_from_db()
        self.assertEqual(self.draft_listing.title, 'Updated Title')

    def test_other_owner_cannot_edit_listing(self):
        self.auth_as(self.other_owner)
        resp = self.client.patch(f'/api/listings/{self.draft_listing.pk}/', {'title': 'Hijacked'})
        self.assertIn(resp.status_code, (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND))
        self.draft_listing.refresh_from_db()
        self.assertNotEqual(self.draft_listing.title, 'Hijacked')

    def test_buyer_cannot_edit_listing(self):
        self.auth_as(self.buyer)
        resp = self.client.patch(f'/api/listings/{self.published_listing.pk}/', {'title': 'Hijacked'})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_can_delete_own_listing(self):
        self.auth_as(self.owner)
        resp = self.client.delete(f'/api/listings/{self.draft_listing.pk}/')
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(HotelListing.objects.filter(pk=self.draft_listing.pk).exists())

    def test_other_owner_cannot_delete_listing(self):
        self.auth_as(self.other_owner)
        resp = self.client.delete(f'/api/listings/{self.draft_listing.pk}/')
        self.assertIn(resp.status_code, (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND))
        self.assertTrue(HotelListing.objects.filter(pk=self.draft_listing.pk).exists())


class ListingStatusTransitionTests(ApiTestBase):
    def test_owner_can_publish_draft_listing(self):
        self.auth_as(self.owner)
        resp = self.client.post(f'/api/listings/{self.draft_listing.pk}/publish/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.draft_listing.refresh_from_db()
        self.assertEqual(self.draft_listing.status, HotelListing.Status.PENDING)

    def test_non_owner_cannot_close_listing(self):
        self.auth_as(self.other_owner)
        resp = self.client.post(f'/api/listings/{self.published_listing.pk}/close/')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.published_listing.refresh_from_db()
        self.assertEqual(self.published_listing.status, HotelListing.Status.PUBLISHED)
