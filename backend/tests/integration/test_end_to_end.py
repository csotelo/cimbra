"""Integration tests for end-to-end flows."""

import pytest
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.tenants.models import Tenant, UserTenantRole
from apps.users.models import CustomUser
from apps.api_tokens.models import APIToken


@pytest.mark.django_db
class TestFullRegistrationFlow:
    """Tests for complete user registration flow."""

    def setup_method(self):
        """Set up test client."""
        self.client = APIClient()
        self.register_url = reverse("register")
        self.login_url = reverse("login")
        self.verify_url = reverse("verify_email")

    def test_complete_registration_flow(self):
        """Test full registration: register -> verify -> login."""
        email = "integration_test@example.com"
        password = "securepassword123"

        register_response = self.client.post(
            self.register_url,
            {"email": email, "password": password},
            format="json",
        )
        assert register_response.status_code == status.HTTP_201_CREATED

        user = CustomUser.objects.get(email=email)
        assert not user.is_email_verified
        assert user.email_verification_token is not None

        verify_response = self.client.get(
            self.verify_url, {"token": user.email_verification_token}
        )
        assert verify_response.status_code == status.HTTP_200_OK

        user.refresh_from_db()
        assert user.is_email_verified

        login_response = self.client.post(
            self.login_url,
            {"email": email, "password": password},
            format="json",
        )
        assert login_response.status_code == status.HTTP_200_OK
        assert "access_token" in login_response.cookies
        assert "refresh_token" in login_response.cookies
        assert "tenant_list" in login_response.data


@pytest.mark.django_db
class TestTenantCreationFlow:
    """Tests for complete tenant creation flow."""

    def setup_method(self):
        """Set up test client and authenticated user."""
        self.client = APIClient()
        self.user = CustomUser.objects.create_user(
            email="tenant_creator@example.com",
            password="password123",
            is_email_verified=True,
        )
        self.client.force_authenticate(user=self.user)

    def test_create_tenant_becomes_owner(self):
        """Test that creating a tenant makes user the owner."""
        tenant_data = {
            "name": "My New Tenant",
            "slug": "my-new-tenant",
        }

        response = self.client.post("/api/tenants/", tenant_data, format="json")
        assert response.status_code == status.HTTP_201_CREATED

        tenant = Tenant.objects.get(slug="my-new-tenant")
        role = UserTenantRole.objects.get(user=self.user, tenant=tenant)
        assert role.role == UserTenantRole.Role.OWNER


@pytest.mark.django_db
class TestTokenGenerationFlow:
    """Tests for complete token generation flow."""

    def setup_method(self):
        """Set up test client, user, and tenant."""
        self.client = APIClient()
        self.user = CustomUser.objects.create_user(
            email="token_owner@example.com",
            password="password123",
            is_email_verified=True,
        )
        self.client.force_authenticate(user=self.user)

        self.tenant = Tenant.objects.create(
            name="Token Tenant",
            slug="token-tenant",
        )
        UserTenantRole.objects.create(
            user=self.user,
            tenant=self.tenant,
            role=UserTenantRole.Role.OWNER,
        )

    def test_generate_token_returns_plain_text(self):
        """Test generating token returns plain text token."""
        response = self.client.post(
            f"/api/tenants/{self.tenant.id}/token/",
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert "token" in response.data
        assert len(response.data["token"]) >= 32

    def test_token_only_shown_once(self):
        """Test token is only shown once at creation."""
        response = self.client.post(
            f"/api/tenants/{self.tenant.id}/token/",
            format="json",
        )
        token = response.data["token"]

        get_response = self.client.get(
            f"/api/tenants/{self.tenant.id}/token/",
        )
        assert get_response.status_code == status.HTTP_200_OK
        assert "token" not in get_response.data

    def test_token_regeneration_revokes_old(self):
        """Test regenerating token revokes the old one."""
        response1 = self.client.post(
            f"/api/tenants/{self.tenant.id}/token/",
            format="json",
        )
        token1 = response1.data["token"]

        response2 = self.client.post(
            f"/api/tenants/{self.tenant.id}/token/",
            format="json",
        )
        token2 = response2.data["token"]

        assert token1 != token2

        old_token = APIToken.objects.filter(
            tenant=self.tenant, owner=self.user, is_active=False
        ).first()
        assert old_token is not None


@pytest.mark.django_db
class TestTenantIsolation:
    """Tests for tenant data isolation."""

    def setup_method(self):
        """Set up two users with separate tenants."""
        self.client = APIClient()

        self.user_a = CustomUser.objects.create_user(
            email="user_a@example.com",
            password="password123",
            is_email_verified=True,
        )
        self.user_b = CustomUser.objects.create_user(
            email="user_b@example.com",
            password="password123",
            is_email_verified=True,
        )

        self.tenant_a = Tenant.objects.create(
            name="Tenant A",
            slug="tenant-a",
        )
        self.tenant_b = Tenant.objects.create(
            name="Tenant B",
            slug="tenant-b",
        )

        UserTenantRole.objects.create(
            user=self.user_a,
            tenant=self.tenant_a,
            role=UserTenantRole.Role.OWNER,
        )
        UserTenantRole.objects.create(
            user=self.user_b,
            tenant=self.tenant_b,
            role=UserTenantRole.Role.OWNER,
        )

    def test_user_a_cannot_see_tenant_b(self):
        """Test user A cannot see tenant B in list."""
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get("/api/tenants/")
        assert response.status_code == status.HTTP_200_OK

        results = response.data.get("results", response.data)
        tenant_ids = [t["id"] for t in results]
        assert str(self.tenant_b.id) not in tenant_ids

    def test_user_a_cannot_access_tenant_b_directly(self):
        """Test user A cannot access tenant B directly."""
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get(f"/api/tenants/{self.tenant_b.id}/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cross_tenant_member_isolation(self):
        """Test members cannot see other tenants' data."""
        member = CustomUser.objects.create_user(
            email="member@example.com",
            password="password123",
            is_email_verified=True,
        )

        UserTenantRole.objects.create(
            user=member,
            tenant=self.tenant_a,
            role=UserTenantRole.Role.MEMBER,
        )

        self.client.force_authenticate(user=member)
        response = self.client.get("/api/tenants/")
        assert response.status_code == status.HTTP_200_OK

        results = response.data.get("results", response.data)
        tenant_ids = [t["id"] for t in results]
        assert str(self.tenant_a.id) in tenant_ids
        assert str(self.tenant_b.id) not in tenant_ids


@pytest.mark.django_db
class TestRolePermissions:
    """Tests for role-based permissions."""

    def setup_method(self):
        """Set up users with different roles."""
        self.client = APIClient()

        self.owner = CustomUser.objects.create_user(
            email="owner@example.com",
            password="password123",
            is_email_verified=True,
        )
        self.admin = CustomUser.objects.create_user(
            email="admin@example.com",
            password="password123",
            is_email_verified=True,
        )
        self.member = CustomUser.objects.create_user(
            email="member@example.com",
            password="password123",
            is_email_verified=True,
        )

        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            slug="test-perms-tenant",
        )

        UserTenantRole.objects.create(
            user=self.owner,
            tenant=self.tenant,
            role=UserTenantRole.Role.OWNER,
        )
        UserTenantRole.objects.create(
            user=self.admin,
            tenant=self.tenant,
            role=UserTenantRole.Role.ADMIN,
        )
        UserTenantRole.objects.create(
            user=self.member,
            tenant=self.tenant,
            role=UserTenantRole.Role.MEMBER,
        )

    def test_owner_can_manage_tenant(self):
        """Test owner can update tenant."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(
            f"/api/tenants/{self.tenant.id}/",
            {"name": "Updated Name"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK

    def test_owner_can_manage_members(self):
        """Test owner can change member roles."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(
            f"/api/tenants/{self.tenant.id}/members/{self.member.id}/role/",
            {"role": "ADMIN"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK

    def test_owner_can_generate_token(self):
        """Test owner can generate API token."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(
            f"/api/tenants/{self.tenant.id}/token/",
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_admin_cannot_change_owner_role(self):
        """Test admin cannot change owner role."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            f"/api/tenants/{self.tenant.id}/members/{self.owner.id}/role/",
            {"role": "MEMBER"},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_cannot_delete_tenant(self):
        """Test admin cannot delete tenant."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(f"/api/tenants/{self.tenant.id}/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_add_members(self):
        """Test admin can add members."""
        new_user = CustomUser.objects.create_user(
            email="new_member@example.com",
            password="password123",
            is_email_verified=True,
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            f"/api/tenants/{self.tenant.id}/members/",
            {"email": new_user.email},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_member_cannot_add_members(self):
        """Test member cannot add members."""
        new_user = CustomUser.objects.create_user(
            email="another_member@example.com",
            password="password123",
            is_email_verified=True,
        )
        self.client.force_authenticate(user=self.member)
        response = self.client.post(
            f"/api/tenants/{self.tenant.id}/members/",
            {"user_id": str(new_user.id), "role": "MEMBER"},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_member_cannot_generate_token(self):
        """Test member cannot generate API token (returns 404 via tenant scope)."""
        self.client.force_authenticate(user=self.member)
        response = self.client.post(
            f"/api/tenants/{self.tenant.id}/token/",
            format="json",
        )
        # TenantAwareManager filters by active tenant context; without an active
        # tenant context the tenant lookup returns 404 before the 403 permission check.
        assert response.status_code in (
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        )


@pytest.mark.django_db
class TestSuperAdminPermissions:
    """Tests for SuperAdmin bypass permissions."""

    def setup_method(self):
        """Set up superadmin and regular users."""
        self.client = APIClient()

        self.superadmin = CustomUser.objects.create_user(
            email="superadmin@example.com",
            password="password123",
            is_email_verified=True,
            is_superuser=True,
            is_staff=True,
        )

        self.owner = CustomUser.objects.create_user(
            email="owner@example.com",
            password="password123",
            is_email_verified=True,
        )

        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            slug="superadmin-test-tenant",
        )
        UserTenantRole.objects.create(
            user=self.owner,
            tenant=self.tenant,
            role=UserTenantRole.Role.OWNER,
        )

    def test_superadmin_can_access_any_tenant(self):
        """Test superadmin can access any tenant."""
        self.client.force_authenticate(user=self.superadmin)
        response = self.client.get(f"/api/tenants/{self.tenant.id}/")
        assert response.status_code == status.HTTP_200_OK

    def test_superadmin_can_list_all_tenants(self):
        """Test superadmin sees all tenants."""
        self.client.force_authenticate(user=self.superadmin)
        response = self.client.get("/api/tenants/")
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get("results", response.data)
        tenant_ids = [t["id"] for t in results]
        assert str(self.tenant.id) in tenant_ids


@pytest.mark.django_db
class TestMemberLimits:
    """Tests for tenant member limits."""

    def setup_method(self):
        """Set up owner with limited tenant."""
        self.client = APIClient()
        self.owner = CustomUser.objects.create_user(
            email="limit_owner@example.com",
            password="password123",
            is_email_verified=True,
        )
        self.client.force_authenticate(user=self.owner)

        self.tenant = Tenant.objects.create(
            name="Limited Tenant",
            slug="limited-tenant",
            max_users=2,
        )
        UserTenantRole.objects.create(
            user=self.owner,
            tenant=self.tenant,
            role=UserTenantRole.Role.OWNER,
        )

    def test_cannot_add_members_over_limit(self):
        """Test cannot add members beyond max_users limit."""
        user1 = CustomUser.objects.create_user(
            email="user1@example.com",
            password="password123",
            is_email_verified=True,
        )
        user2 = CustomUser.objects.create_user(
            email="user2@example.com",
            password="password123",
            is_email_verified=True,
        )

        self.client.post(
            f"/api/tenants/{self.tenant.id}/members/",
            {"user_id": str(user1.id), "role": "MEMBER"},
            format="json",
        )
        response = self.client.post(
            f"/api/tenants/{self.tenant.id}/members/",
            {"user_id": str(user2.id), "role": "MEMBER"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
