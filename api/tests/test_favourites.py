from rest_framework import status

from listings.models import Favourite
from .base import ApiTestBase


class FavouriteTests(ApiTestBase):
    def test_anonymous_cannot_list_favourites(self):
        resp = self.client.get('/api/favourites/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_buyer_can_save_published_listing(self):
        self.auth_as(self.buyer)
        resp = self.client.post('/api/favourites/', {'listing': self.published_listing.pk})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        self.assertTrue(Favourite.objects.filter(buyer=self.buyer, listing=self.published_listing).exists())

    def test_owner_cannot_save_a_listing(self):
        self.auth_as(self.owner)
        resp = self.client.post('/api/favourites/', {'listing': self.published_listing.pk})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_favourite_a_draft_listing(self):
        self.auth_as(self.buyer)
        resp = self.client.post('/api/favourites/', {'listing': self.draft_listing.pk})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_buyer_only_sees_own_favourites(self):
        fav = Favourite.objects.create(buyer=self.buyer, listing=self.published_listing)
        self.auth_as(self.other_buyer)
        resp = self.client.get('/api/favourites/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data['results']), 0)

        self.auth_as(self.buyer)
        resp = self.client.get('/api/favourites/')
        self.assertEqual(len(resp.data['results']), 1)
        self.assertEqual(resp.data['results'][0]['id'], fav.id)

    def test_buyer_can_remove_own_favourite(self):
        fav = Favourite.objects.create(buyer=self.buyer, listing=self.published_listing)
        self.auth_as(self.buyer)
        resp = self.client.delete(f'/api/favourites/{fav.pk}/')
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Favourite.objects.filter(pk=fav.pk).exists())

    def test_buyer_cannot_remove_someone_elses_favourite(self):
        fav = Favourite.objects.create(buyer=self.buyer, listing=self.published_listing)
        self.auth_as(self.other_buyer)
        resp = self.client.delete(f'/api/favourites/{fav.pk}/')
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Favourite.objects.filter(pk=fav.pk).exists())
