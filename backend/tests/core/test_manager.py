"""Tests for TenantAwareManager with real BaseModel inheritance."""

from django.test import TestCase

from apps.api_tokens.models import APIToken
from apps.tenants.models import Tenant, UserTenantRole
from apps.users.models import CustomUser
from core.middleware import set_current_tenant, set_current_user


class TenantAwareManagerTest(TestCase):
    """Test TenantAwareManager filtering with APIToken (real BaseModel subclass)."""

    def setUp(self):
        """Create tenants, users, and test objects."""
        self.tenant_a = Tenant.objects.create(
            name="Tenant A",
            slug="tenant-a",
        )
        self.tenant_b = Tenant.objects.create(
            name="Tenant B",
            slug="tenant-b",
        )
        self.owner = CustomUser.objects.create_user(
            email="owner@example.com",
            password="testpass123",
        )
        UserTenantRole.objects.create(
            user=self.owner,
            tenant=self.tenant_a,
            role=UserTenantRole.Role.OWNER,
        )
        UserTenantRole.objects.create(
            user=self.owner,
            tenant=self.tenant_b,
            role=UserTenantRole.Role.OWNER,
        )
        self.token_a = APIToken.create_for_tenant(
            tenant=self.tenant_a,
            owner=self.owner,
        )
        self.token_b = APIToken.create_for_tenant(
            tenant=self.tenant_b,
            owner=self.owner,
        )

    def tearDown(self):
        """Clear thread-local context."""
        set_current_tenant(None)
        set_current_user(None)

    def test_get_queryset_filters_by_current_tenant(self):
        """get_queryset returns only objects for the current tenant."""
        set_current_tenant(self.tenant_a)
        results = list(APIToken.objects.all())
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, self.token_a.id)
        self.assertNotIn(self.token_b, results)

    def test_get_queryset_no_tenant_returns_all(self):
        """get_queryset returns all objects when no tenant is set."""
        set_current_tenant(None)
        results = list(APIToken.objects.all())
        self.assertEqual(len(results), 2)

    def test_for_tenant_specific_filter(self):
        """for_tenant returns objects for a specific tenant regardless of context."""
        set_current_tenant(self.tenant_a)
        results = list(APIToken.objects.for_tenant(self.tenant_b))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, self.token_b.id)

    def test_all_tenants_bypasses_context(self):
        """all_tenants returns all objects ignoring tenant context."""
        set_current_tenant(self.tenant_a)
        results = list(APIToken.objects.all_tenants())
        self.assertEqual(len(results), 2)


class UserTenantRoleTest(TestCase):
    """Test UserTenantRole functionality."""

    def setUp(self):
        """Create tenant and user."""
        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            slug="test-tenant",
        )
        self.user = CustomUser.objects.create_user(
            email="member@example.com",
            password="testpass123",
        )

    def test_create_membership(self):
        """Verify membership is created correctly."""
        membership = UserTenantRole.objects.create(
            user=self.user,
            tenant=self.tenant,
            role=UserTenantRole.Role.MEMBER,
        )
        self.assertEqual(membership.role, UserTenantRole.Role.MEMBER)
        self.assertEqual(
            str(membership),
            f"{self.user.email} - Test Tenant (MEMBER)",
        )

    def test_user_role_checks(self):
        """Verify user role check methods work."""
        UserTenantRole.objects.create(
            user=self.user,
            tenant=self.tenant,
            role=UserTenantRole.Role.ADMIN,
        )
        self.assertTrue(self.user.is_admin_of(self.tenant))
        self.assertFalse(self.user.is_member_of(self.tenant))
        self.assertFalse(self.user.is_owner_of(self.tenant))


class TenantModelTest(TestCase):
    """Test Tenant model defaults and methods."""

    def test_tenant_defaults(self):
        """Verify tenant is created with correct defaults."""
        tenant = Tenant.objects.create(name="Test", slug="test")
        self.assertEqual(tenant.name, "Test")
        self.assertTrue(tenant.is_active)
        self.assertEqual(tenant.max_users, 10)
        self.assertTrue(tenant.can_add_user())

    def test_can_add_user_logic(self):
        """Verify can_add_user respects max_users limit."""
        tenant = Tenant.objects.create(name="Small", slug="small", max_users=1)
        self.assertTrue(tenant.can_add_user())

        user = CustomUser.objects.create_user(
            email="only@example.com",
            password="testpass123",
        )
        UserTenantRole.objects.create(
            user=user,
            tenant=tenant,
            role=UserTenantRole.Role.MEMBER,
        )
        self.assertFalse(tenant.can_add_user())


class CustomUserModelTest(TestCase):
    """Test CustomUser model."""

    def test_user_creation(self):
        """Verify user is created with correct defaults."""
        user = CustomUser.objects.create_user(
            email="test@example.com",
            password="testpass123",
        )
        self.assertEqual(user.email, "test@example.com")
        self.assertFalse(user.is_email_verified)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_superuser)

    def test_password_hashing(self):
        """Verify user password is hashed correctly."""
        user = CustomUser.objects.create_user(
            email="test@example.com",
            password="testpass123",
        )
        self.assertTrue(user.check_password("testpass123"))
        self.assertFalse(user.check_password("wrongpassword"))

    def test_superuser_creation(self):
        """Verify superuser has correct flags."""
        user = CustomUser.objects.create_superuser(
            email="admin@example.com",
            password="admin123",
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_email_verified)
