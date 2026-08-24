from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token

from .base import ApiTestBase

User = get_user_model()


class RegistrationTests(ApiTestBase):
    def test_register_owner_creates_account_and_profile(self):
        resp = self.client.post('/api/auth/register/', {
            'username': 'newowner', 'email': 'newowner@test.com',
            'password': 'StrongPass123', 'role': 'owner', 'business_name': 'New Co',
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        self.assertIn('token', resp.data)
        user = User.objects.get(username='newowner')
        self.assertEqual(user.role, User.Role.OWNER)
        self.assertTrue(user.check_password('StrongPass123'))
        self.assertTrue(hasattr(user, 'owner_profile'))

    def test_register_buyer_creates_account_and_profile(self):
        resp = self.client.post('/api/auth/register/', {
            'username': 'newbuyer', 'email': 'newbuyer@test.com',
            'password': 'StrongPass123', 'role': 'buyer', 'company_name': 'Capital LLC',
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        user = User.objects.get(username='newbuyer')
        self.assertEqual(user.role, User.Role.BUYER)
        self.assertTrue(hasattr(user, 'buyer_profile'))

    def test_passwords_are_hashed_not_stored_in_plaintext(self):
        self.client.post('/api/auth/register/', {
            'username': 'hashcheck', 'email': 'hashcheck@test.com',
            'password': 'StrongPass123', 'role': 'buyer',
        })
        user = User.objects.get(username='hashcheck')
        self.assertNotEqual(user.password, 'StrongPass123')
        self.assertTrue(user.password.startswith('pbkdf2_'))

    def test_duplicate_email_rejected(self):
        self.client.post('/api/auth/register/', {
            'username': 'dupe1', 'email': 'dupe@test.com',
            'password': 'StrongPass123', 'role': 'buyer',
        })
        resp = self.client.post('/api/auth/register/', {
            'username': 'dupe2', 'email': 'dupe@test.com',
            'password': 'StrongPass123', 'role': 'buyer',
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_weak_password_rejected(self):
        resp = self.client.post('/api/auth/register/', {
            'username': 'weakpw', 'email': 'weakpw@test.com',
            'password': '123', 'role': 'buyer',
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class LoginTests(ApiTestBase):
    def test_login_with_valid_credentials_returns_token(self):
        resp = self.client.post('/api/auth/login/', {
            'username': 'buyer1', 'password': 'Password123',
        })
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('token', resp.data)
        self.assertEqual(resp.data['user']['username'], 'buyer1')
        self.assertTrue(Token.objects.filter(key=resp.data['token'], user=self.buyer).exists())

    def test_login_with_invalid_password_rejected(self):
        resp = self.client.post('/api/auth/login/', {
            'username': 'buyer1', 'password': 'WrongPassword',
        })
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_with_suspended_account_rejected(self):
        self.buyer.is_active = False
        self.buyer.status = User.Status.SUSPENDED
        self.buyer.save()
        resp = self.client.post('/api/auth/login/', {
            'username': 'buyer1', 'password': 'Password123',
        })
        self.assertIn(resp.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_logout_invalidates_token(self):
        self.auth_as(self.buyer)
        Token.objects.get_or_create(user=self.buyer)
        resp = self.client.post('/api/auth/logout/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(Token.objects.filter(user=self.buyer).exists())


class MeEndpointTests(ApiTestBase):
    def test_anonymous_cannot_access_me(self):
        resp = self.client.get('/api/users/me/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_can_view_own_profile(self):
        self.auth_as(self.buyer)
        resp = self.client.get('/api/users/me/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['username'], 'buyer1')
        self.assertEqual(resp.data['role'], 'buyer')

    def test_user_can_update_own_basic_details(self):
        self.auth_as(self.buyer)
        resp = self.client.patch('/api/users/me/', {'first_name': 'Updated'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.buyer.refresh_from_db()
        self.assertEqual(self.buyer.first_name, 'Updated')


class AdminRouteProtectionTests(ApiTestBase):
    def test_anonymous_cannot_access_admin_users(self):
        resp = self.client.get('/api/admin/users/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_admin_cannot_access_admin_users(self):
        self.auth_as(self.buyer)
        resp = self.client.get('/api/admin/users/')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_cannot_access_admin_listings(self):
        self.auth_as(self.owner)
        resp = self.client.get('/api/admin/listings/')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_access_admin_users(self):
        self.auth_as(self.admin)
        resp = self.client.get('/api/admin/users/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_admin_can_moderate_a_pending_listing(self):
        self.draft_listing.status = 'pending'
        self.draft_listing.save()
        self.auth_as(self.admin)
        resp = self.client.post(f'/api/admin/listings/{self.draft_listing.pk}/moderate/', {'action': 'approve'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.draft_listing.refresh_from_db()
        self.assertEqual(self.draft_listing.status, 'published')
