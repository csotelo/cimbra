"""Tests for API token management."""

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.api_tokens.models import APIToken
from apps.tenants.models import Tenant, UserTenantRole
from apps.users.models import CustomUser


class APITokenModelTests(TestCase):
    """Tests for APIToken model."""

    def setUp(self):
        """Set up test data."""
        self.user = CustomUser.objects.create_user(
            email="owner@example.com",
            password="password123",
        )
        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            slug="test-tenant",
        )
        UserTenantRole.objects.create(
            user=self.user,
            tenant=self.tenant,
            role=UserTenantRole.Role.OWNER,
        )

    def test_create_token(self):
        """Test token creation."""
        token = APIToken.create_for_tenant(self.tenant, self.user)
        self.assertIsNotNone(token.token)
        self.assertEqual(len(token.token), 43)
        self.assertTrue(token.is_active)
        self.assertFalse(token.is_expired)

    def test_only_one_active_token_per_owner_tenant(self):
        """Test that only one active token per owner-tenant is allowed."""
        token1 = APIToken.create_for_tenant(self.tenant, self.user)
        token2 = APIToken.create_for_tenant(self.tenant, self.user)

        token1.refresh_from_db()
        self.assertFalse(token1.is_active)
        self.assertTrue(token2.is_active)
        self.assertEqual(
            APIToken.objects.filter(
                tenant=self.tenant,
                owner=self.user,
                is_active=True,
            ).count(),
            1,
        )

    def test_token_expiration(self):
        """Test token expiration."""
        from django.utils import timezone
        from datetime import timedelta

        token = APIToken.create_for_tenant(self.tenant, self.user)
        token.expires_at = timezone.now() - timedelta(days=1)
        token.save()

        self.assertTrue(token.is_expired)
        self.assertFalse(token.is_valid)

    def test_revoke_token(self):
        """Test token revocation."""
        token = APIToken.create_for_tenant(self.tenant, self.user)
        token.revoke()

        token.refresh_from_db()
        self.assertFalse(token.is_active)
        self.assertFalse(token.is_valid)


class APITokenViewTests(TestCase):
    """Tests for API token endpoints."""

    def setUp(self):
        """Set up test clients and users."""
        self.client = APIClient()

        self.owner = CustomUser.objects.create_user(
            email="owner@example.com",
            password="password123",
        )

        self.member = CustomUser.objects.create_user(
            email="member@example.com",
            password="password123",
        )

        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            slug="test-tenant",
            is_active=True,
        )

        UserTenantRole.objects.create(
            user=self.owner,
            tenant=self.tenant,
            role=UserTenantRole.Role.OWNER,
        )

        UserTenantRole.objects.create(
            user=self.member,
            tenant=self.tenant,
            role=UserTenantRole.Role.MEMBER,
        )

    def test_owner_can_create_token(self):
        """Test owner can create a token."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(
            f"/api/tenants/{self.tenant.id}/token/",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("token", response.data)
        self.assertIn("expires_at", response.data)

    def test_member_cannot_create_token(self):
        """Test member cannot create a token."""
        self.client.force_authenticate(user=self.member)
        response = self.client.post(
            f"/api/tenants/{self.tenant.id}/token/",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_owner_can_view_token_status(self):
        """Test owner can view token status."""
        APIToken.create_for_tenant(self.tenant, self.owner)

        self.client.force_authenticate(user=self.owner)
        response = self.client.get(
            f"/api/tenants/{self.tenant.id}/token/",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("token", response.data)

    def test_owner_can_revoke_token(self):
        """Test owner can revoke a token."""
        APIToken.create_for_tenant(self.tenant, self.owner)

        self.client.force_authenticate(user=self.owner)
        response = self.client.delete(
            f"/api/tenants/{self.tenant.id}/token/",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        token = APIToken.objects.get(
            tenant=self.tenant,
            owner=self.owner,
        )
        self.assertFalse(token.is_active)

    def test_token_regenerated_after_revoke(self):
        """Test that a new token is created after revoking."""
        token1 = APIToken.create_for_tenant(self.tenant, self.owner)

        self.client.force_authenticate(user=self.owner)
        response = self.client.post(
            f"/api/tenants/{self.tenant.id}/token/",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(response.data["token"], token1.token)

    def test_cannot_view_other_tenant_token(self):
        """Test cannot view token for tenant you don't own."""
        other_owner = CustomUser.objects.create_user(
            email="other@example.com",
            password="password123",
        )
        other_tenant = Tenant.objects.create(
            name="Other Tenant",
            slug="other-tenant",
        )
        UserTenantRole.objects.create(
            user=other_owner,
            tenant=other_tenant,
            role=UserTenantRole.Role.OWNER,
        )

        self.client.force_authenticate(user=self.owner)
        response = self.client.get(
            f"/api/tenants/{other_tenant.id}/token/",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_cannot_access(self):
        """Test unauthenticated user cannot access token endpoints."""
        response = self.client.post(
            f"/api/tenants/{self.tenant.id}/token/",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
