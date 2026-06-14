"""Tests for tenant CRUD and member management."""

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.tenants.models import Tenant, UserTenantRole
from apps.users.models import CustomUser


class TenantTests(TestCase):
    """Tests for tenant CRUD operations."""

    def setUp(self):
        """Set up test clients and users."""
        self.client = APIClient()

        self.user = CustomUser.objects.create_user(
            email="owner@example.com",
            password="password123",
        )

        self.member_user = CustomUser.objects.create_user(
            email="member@example.com",
            password="password123",
        )

        self.superadmin = CustomUser.objects.create_superuser(
            email="superadmin@example.com",
            password="password123",
        )

        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            slug="test-tenant",
            is_active=True,
            max_users=10,
        )

        UserTenantRole.objects.create(
            user=self.user,
            tenant=self.tenant,
            role=UserTenantRole.Role.OWNER,
        )

        UserTenantRole.objects.create(
            user=self.member_user,
            tenant=self.tenant,
            role=UserTenantRole.Role.MEMBER,
        )

    def test_owner_can_list_tenants(self):
        """Test owner can list their tenants."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/tenants/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_member_can_list_tenants(self):
        """Test member can list tenants they belong to."""
        self.client.force_authenticate(user=self.member_user)
        response = self.client.get("/api/tenants/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_non_member_cannot_list_tenants(self):
        """Test non-member cannot see tenant."""
        other_user = CustomUser.objects.create_user(
            email="other@example.com",
            password="password123",
        )
        self.client.force_authenticate(user=other_user)
        response = self.client.get("/api/tenants/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)

    def test_superadmin_can_list_all_tenants(self):
        """Test superadmin can see all tenants."""
        self.client.force_authenticate(user=self.superadmin)
        response = self.client.get("/api/tenants/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data["results"]), 1)

    def test_owner_can_create_tenant(self):
        """Test owner can create new tenant."""
        self.client.force_authenticate(user=self.user)
        data = {"name": "New Tenant"}
        response = self.client.post("/api/tenants/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "New Tenant")

    def test_owner_becomes_owner_of_new_tenant(self):
        """Test creator becomes owner of new tenant."""
        self.client.force_authenticate(user=self.user)
        data = {"name": "Another Tenant"}
        response = self.client.post("/api/tenants/", data, format="json")

        new_tenant = Tenant.objects.get(slug=response.data["slug"])
        is_owner = UserTenantRole.objects.filter(
            user=self.user,
            tenant=new_tenant,
            role=UserTenantRole.Role.OWNER,
        ).exists()
        self.assertTrue(is_owner)

    def test_any_authenticated_user_can_create_tenant(self):
        """Test any authenticated user can create a tenant and becomes owner."""
        self.client.force_authenticate(user=self.member_user)
        data = {"name": "New Tenant"}
        response = self.client.post("/api/tenants/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_owner_can_update_tenant(self):
        """Test owner can update tenant."""
        self.client.force_authenticate(user=self.user)
        data = {"name": "Updated Name"}
        response = self.client.patch(
            f"/api/tenants/{self.tenant.id}/",
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.tenant.refresh_from_db()
        self.assertEqual(self.tenant.name, "Updated Name")

    def test_member_cannot_update_tenant(self):
        """Test member cannot update tenant."""
        self.client.force_authenticate(user=self.member_user)
        data = {"name": "Unauthorized Update"}
        response = self.client.patch(
            f"/api/tenants/{self.tenant.id}/",
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_can_delete_tenant(self):
        """Test owner can soft delete tenant."""
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f"/api/tenants/{self.tenant.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.tenant.refresh_from_db()
        self.assertFalse(self.tenant.is_active)

    def test_member_cannot_delete_tenant(self):
        """Test member cannot delete tenant."""
        self.client.force_authenticate(user=self.member_user)
        response = self.client.delete(f"/api/tenants/{self.tenant.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TenantMemberTests(TestCase):
    """Tests for tenant member management."""

    def setUp(self):
        """Set up test clients and users."""
        self.client = APIClient()

        self.owner = CustomUser.objects.create_user(
            email="owner@example.com",
            password="password123",
        )

        self.admin = CustomUser.objects.create_user(
            email="admin@example.com",
            password="password123",
        )

        self.member = CustomUser.objects.create_user(
            email="member@example.com",
            password="password123",
        )

        self.other_user = CustomUser.objects.create_user(
            email="other@example.com",
            password="password123",
        )

        self.superadmin = CustomUser.objects.create_superuser(
            email="superadmin@example.com",
            password="password123",
        )

        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            slug="test-tenant",
            is_active=True,
            max_users=10,
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

    def test_owner_can_list_members(self):
        """Test owner can list members."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(
            f"/api/tenants/{self.tenant.id}/members/",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_member_can_list_members(self):
        """Test member can list members."""
        self.client.force_authenticate(user=self.member)
        response = self.client.get(
            f"/api/tenants/{self.tenant.id}/members/",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_owner_can_add_member(self):
        """Test owner can add new member."""
        new_user = CustomUser.objects.create_user(
            email="newmember@example.com",
            password="password123",
        )
        self.client.force_authenticate(user=self.owner)
        data = {"email": "newmember@example.com"}
        response = self.client.post(
            f"/api/tenants/{self.tenant.id}/members/",
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_admin_can_add_member(self):
        new_user = CustomUser.objects.create_user(
            email="newmember2@example.com",
            password="password123",
        )
        self.client.force_authenticate(user=self.admin)
        data = {"email": "newmember2@example.com"}
        response = self.client.post(
            f"/api/tenants/{self.tenant.id}/members/",
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_member_cannot_add_member(self):
        """Test regular member cannot add new member."""
        self.client.force_authenticate(user=self.member)
        data = {"email": "unauthorized@example.com"}
        response = self.client.post(
            f"/api/tenants/{self.tenant.id}/members/",
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_can_remove_member(self):
        """Test owner can remove member."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.delete(
            f"/api/tenants/{self.tenant.id}/members/{self.member.id}/",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_can_remove_member(self):
        """Test admin can remove member."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(
            f"/api/tenants/{self.tenant.id}/members/{self.member.id}/",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cannot_remove_owner(self):
        """Test cannot remove owner."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.delete(
            f"/api/tenants/{self.tenant.id}/members/{self.owner.id}/",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_member_cannot_remove_member(self):
        """Test member cannot remove other member."""
        self.client.force_authenticate(user=self.member)
        response = self.client.delete(
            f"/api/tenants/{self.tenant.id}/members/{self.admin.id}/",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_can_change_member_role(self):
        """Test owner can change member role."""
        self.client.force_authenticate(user=self.owner)
        data = {"role": "ADMIN"}
        response = self.client.patch(
            f"/api/tenants/{self.tenant.id}/members/{self.member.id}/role/",
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["role"], "ADMIN")

    def test_admin_cannot_change_member_role(self):
        """Test admin cannot change member role."""
        self.client.force_authenticate(user=self.admin)
        data = {"role": "ADMIN"}
        response = self.client.patch(
            f"/api/tenants/{self.tenant.id}/members/{self.member.id}/role/",
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_change_own_role(self):
        """Test user cannot change their own role."""
        self.client.force_authenticate(user=self.owner)
        data = {"role": "MEMBER"}
        response = self.client.patch(
            f"/api/tenants/{self.tenant.id}/members/{self.owner.id}/role/",
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_change_owner_role(self):
        """Test cannot change owner's role."""
        self.client.force_authenticate(user=self.owner)
        data = {"role": "MEMBER"}
        response = self.client.patch(
            f"/api/tenants/{self.tenant.id}/members/{self.owner.id}/role/",
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_superadmin_can_do_everything(self):
        """Test superadmin bypasses all restrictions."""
        new_user = CustomUser.objects.create_user(
            email="newmember3@example.com",
            password="password123",
        )
        self.client.force_authenticate(user=self.superadmin)

        response = self.client.get(
            f"/api/tenants/{self.tenant.id}/members/",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = {"email": "newmember3@example.com"}
        response = self.client.post(
            f"/api/tenants/{self.tenant.id}/members/",
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class TenantLimitsTests(TestCase):
    """Tests for tenant limits enforcement."""

    def setUp(self):
        """Set up test clients and users."""
        self.client = APIClient()

        self.user = CustomUser.objects.create_user(
            email="user@example.com",
            password="password123",
        )

        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            slug="test-tenant",
            is_active=True,
            max_users=2,
        )

    def test_max_tenants_per_user_enforced(self):
        """Test MAX_TENANTS_PER_USER limit is enforced."""
        for i in range(5):
            tenant = Tenant.objects.create(
                name=f"Tenant {i}",
                slug=f"tenant-{i}",
            )
            UserTenantRole.objects.create(
                user=self.user,
                tenant=tenant,
                role=UserTenantRole.Role.OWNER,
            )

        self.client.force_authenticate(user=self.user)
        data = {"name": "Sixth Tenant"}
        response = self.client.post("/api/tenants/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_max_users_per_tenant_enforced(self):
        """Test tenant max_users limit is enforced."""
        UserTenantRole.objects.create(
            user=self.user,
            tenant=self.tenant,
            role=UserTenantRole.Role.OWNER,
        )

        user1 = CustomUser.objects.create_user(
            email="user1@example.com",
            password="password123",
        )
        user2 = CustomUser.objects.create_user(
            email="user2@example.com",
            password="password123",
        )

        UserTenantRole.objects.create(
            user=user1,
            tenant=self.tenant,
            role=UserTenantRole.Role.MEMBER,
        )
        UserTenantRole.objects.create(
            user=user2,
            tenant=self.tenant,
            role=UserTenantRole.Role.MEMBER,
        )

        self.client.force_authenticate(user=self.user)
        data = {"email": "user3@example.com"}
        response = self.client.post(
            f"/api/tenants/{self.tenant.id}/members/",
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_add_member_to_inactive_tenant(self):
        """Test cannot add members to inactive tenant."""
        UserTenantRole.objects.create(
            user=self.user,
            tenant=self.tenant,
            role=UserTenantRole.Role.OWNER,
        )

        self.tenant.is_active = False
        self.tenant.save()

        self.client.force_authenticate(user=self.user)
        data = {"email": "newmember@example.com"}
        response = self.client.post(
            f"/api/tenants/{self.tenant.id}/members/",
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
