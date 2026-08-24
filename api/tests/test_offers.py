from rest_framework import status

from offers.models import Offer
from .base import ApiTestBase


class OfferSubmissionTests(ApiTestBase):
    def test_anonymous_cannot_submit_offer(self):
        resp = self.client.post('/api/offers/', {'listing': self.published_listing.pk, 'amount': '4500000'})
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_owner_cannot_submit_offer(self):
        self.auth_as(self.owner)
        resp = self.client.post('/api/offers/', {'listing': self.published_listing.pk, 'amount': '4500000'})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_buyer_can_submit_offer_on_published_listing(self):
        self.auth_as(self.buyer)
        resp = self.client.post('/api/offers/', {'listing': self.published_listing.pk, 'amount': '4500000'})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        offer = Offer.objects.get(pk=resp.data['id'])
        self.assertEqual(offer.buyer, self.buyer)
        self.assertEqual(offer.owner, self.owner)
        self.assertEqual(offer.status, Offer.Status.PENDING)
        self.assertEqual(offer.history.count(), 1)

    def test_buyer_cannot_submit_offer_on_closed_listing(self):
        self.auth_as(self.buyer)
        resp = self.client.post('/api/offers/', {'listing': self.closed_listing.pk, 'amount': '8000000'})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_buyer_cannot_submit_offer_on_draft_listing(self):
        self.auth_as(self.buyer)
        resp = self.client.post('/api/offers/', {'listing': self.draft_listing.pk, 'amount': '1500000'})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_buyer_cannot_submit_duplicate_active_offer(self):
        self.auth_as(self.buyer)
        self.client.post('/api/offers/', {'listing': self.published_listing.pk, 'amount': '4500000'})
        resp = self.client.post('/api/offers/', {'listing': self.published_listing.pk, 'amount': '4700000'})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class OfferActionTests(ApiTestBase):
    def setUp(self):
        super().setUp()
        self.offer = Offer.objects.create(
            listing=self.published_listing, buyer=self.buyer, owner=self.owner, amount=4500000,
        )

    def test_only_participants_can_view_offer(self):
        # The queryset is scoped to the caller's own offers, so a stranger's
        # offer isn't visible to look up at all -> 404 rather than 403.
        self.auth_as(self.other_buyer)
        resp = self.client.get(f'/api/offers/{self.offer.pk}/')
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

        self.auth_as(self.buyer)
        resp = self.client.get(f'/api/offers/{self.offer.pk}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_owner_can_accept_offer(self):
        self.auth_as(self.owner)
        resp = self.client.post(f'/api/offers/{self.offer.pk}/respond/', {'action': 'accept'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.offer.refresh_from_db()
        self.assertEqual(self.offer.status, Offer.Status.ACCEPTED)

    def test_buyer_cannot_accept_own_offer(self):
        self.auth_as(self.buyer)
        resp = self.client.post(f'/api/offers/{self.offer.pk}/respond/', {'action': 'accept'})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.offer.refresh_from_db()
        self.assertEqual(self.offer.status, Offer.Status.PENDING)

    def test_owner_can_counter_offer(self):
        self.auth_as(self.owner)
        resp = self.client.post(f'/api/offers/{self.offer.pk}/respond/', {'action': 'counter', 'amount': '4800000'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.offer.refresh_from_db()
        self.assertEqual(self.offer.status, Offer.Status.COUNTERED)
        self.assertEqual(str(self.offer.amount), '4800000.00')

    def test_buyer_can_withdraw_own_offer(self):
        self.auth_as(self.buyer)
        resp = self.client.post(f'/api/offers/{self.offer.pk}/respond/', {'action': 'withdraw'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.offer.refresh_from_db()
        self.assertEqual(self.offer.status, Offer.Status.WITHDRAWN)

    def test_owner_cannot_withdraw_buyers_offer(self):
        self.auth_as(self.owner)
        resp = self.client.post(f'/api/offers/{self.offer.pk}/respond/', {'action': 'withdraw'})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_mine_and_received_lists_scope_correctly(self):
        self.auth_as(self.buyer)
        resp = self.client.get('/api/offers/mine/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data['results']), 1)

        self.auth_as(self.owner)
        resp = self.client.get('/api/offers/received/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data['results']), 1)

        self.auth_as(self.other_buyer)
        resp = self.client.get('/api/offers/mine/')
        self.assertEqual(len(resp.data['results']), 0)
