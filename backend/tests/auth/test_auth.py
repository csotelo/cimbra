"""Tests for authentication flows."""

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


class RegisterViewTests(TestCase):
    """Tests for user registration endpoint."""

    def setUp(self):
        """Set up test client."""
        self.client = APIClient()
        self.register_url = reverse("register")

    def test_register_success(self):
        """Test successful user registration."""
        data = {
            "email": "newuser@example.com",
            "password": "securepassword123",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("detail", response.data)

    def test_register_duplicate_email(self):
        """Test registration with duplicate email fails."""
        from apps.users.models import CustomUser

        CustomUser.objects.create_user(
            email="existing@example.com",
            password="password123",
        )

        data = {
            "email": "existing@example.com",
            "password": "password123",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_invalid_email(self):
        """Test registration with invalid email fails."""
        data = {
            "email": "invalid-email",
            "password": "password123",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_short_password(self):
        """Test registration with short password fails."""
        data = {
            "email": "user@example.com",
            "password": "short",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginViewTests(TestCase):
    """Tests for login endpoint."""

    def setUp(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.login_url = reverse("login")
        self.user = self._create_user()

    def _create_user(self):
        """Create a test user."""
        from apps.users.models import CustomUser

        return CustomUser.objects.create_user(
            email="testuser@example.com",
            password="testpassword123",
        )

    def test_login_success(self):
        """Test successful login returns tokens in body and as httpOnly cookies."""
        data = {
            "email": "testuser@example.com",
            "password": "testpassword123",
        }
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertIn("access_token", response.cookies)
        self.assertIn("refresh_token", response.cookies)
        self.assertIn("tenant_list", response.data)

    def test_login_wrong_password(self):
        """Test login with wrong password fails."""
        data = {
            "email": "testuser@example.com",
            "password": "wrongpassword",
        }
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_nonexistent_user(self):
        """Test login with nonexistent user fails."""
        data = {
            "email": "nonexistent@example.com",
            "password": "password123",
        }
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class VerifyEmailTests(TestCase):
    """Tests for email verification endpoint."""

    def setUp(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.verify_url = reverse("verify_email")
        self.user = self._create_user()

    def _create_user(self):
        """Create a test user with verification token."""
        from apps.users.models import CustomUser

        user = CustomUser.objects.create_user(
            email="testuser@example.com",
            password="password123",
            is_email_verified=False,
        )
        user.generate_email_verification_token()
        return user

    def test_verify_email_success(self):
        """Test successful email verification."""
        response = self.client.get(
            self.verify_url,
            {"token": self.user.email_verification_token},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db()
        self.assertTrue(self.user.is_email_verified)

    def test_verify_email_invalid_token(self):
        """Test verification with invalid token fails."""
        response = self.client.get(
            self.verify_url,
            {"token": "invalid-token"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_email_missing_token(self):
        """Test verification without token fails."""
        response = self.client.get(self.verify_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ForgotPasswordTests(TestCase):
    """Tests for forgot password endpoint."""

    def setUp(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.forgot_url = reverse("forgot_password")
        self.user = self._create_user()

    def _create_user(self):
        """Create a test user."""
        from apps.users.models import CustomUser

        return CustomUser.objects.create_user(
            email="testuser@example.com",
            password="password123",
        )

    def test_forgot_password_success(self):
        """Test forgot password returns success."""
        data = {"email": "testuser@example.com"}
        response = self.client.post(self.forgot_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_forgot_password_nonexistent_user(self):
        """Test forgot password with nonexistent user still returns 200 (prevents email enumeration)."""
        data = {"email": "nonexistent@example.com"}
        response = self.client.post(self.forgot_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ChangePasswordTests(TestCase):
    """Tests for change password endpoint."""

    def setUp(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.change_url = reverse("change_password")
        self.user = self._create_user()
        self.client.force_authenticate(user=self.user)

    def _create_user(self):
        """Create a test user."""
        from apps.users.models import CustomUser

        return CustomUser.objects.create_user(
            email="testuser@example.com",
            password="oldpassword123",
        )

    def test_change_password_success(self):
        """Test successful password change."""
        data = {
            "current_password": "oldpassword123",
            "new_password": "newpassword456",
            "confirm_password": "newpassword456",
        }
        response = self.client.post(self.change_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newpassword456"))

    def test_change_password_wrong_current(self):
        """Test change password with wrong current password fails."""
        data = {
            "current_password": "wrongpassword",
            "new_password": "newpassword456",
            "confirm_password": "newpassword456",
        }
        response = self.client.post(self.change_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_mismatch(self):
        """Test change password with mismatched confirmation fails."""
        data = {
            "current_password": "oldpassword123",
            "new_password": "newpassword456",
            "confirm_password": "differentpassword",
        }
        response = self.client.post(self.change_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_unauthenticated(self):
        """Test change password without authentication fails."""
        self.client.force_authenticate(user=None)
        data = {
            "current_password": "oldpassword123",
            "new_password": "newpassword456",
            "confirm_password": "newpassword456",
        }
        response = self.client.post(self.change_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ProfileViewTests(TestCase):
    """Tests for profile endpoint."""

    def setUp(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.profile_url = reverse("profile")
        self.user = self._create_user()
        self.client.force_authenticate(user=self.user)

    def _create_user(self):
        """Create a test user."""
        from apps.users.models import CustomUser

        return CustomUser.objects.create_user(
            email="testuser@example.com",
            password="password123",
            is_email_verified=True,
        )

    def test_get_profile_success(self):
        """Test getting user profile."""
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "testuser@example.com")

    def test_get_profile_unauthenticated(self):
        """Test getting profile without authentication fails."""
        self.client.force_authenticate(user=None)
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class SelectTenantTests(TestCase):
    """Tests for select tenant endpoint."""

    def setUp(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.select_url = reverse("select_tenant")
        self.user = self._create_user()
        self.client.force_authenticate(user=self.user)

    def _create_user(self):
        """Create a test user."""
        from apps.users.models import CustomUser

        return CustomUser.objects.create_user(
            email="testuser@example.com",
            password="password123",
        )

    def _create_tenant(self, name, slug):
        """Create a test tenant."""
        from apps.tenants.models import Tenant

        return Tenant.objects.create(name=name, slug=slug)

    def _add_user_to_tenant(self, user, tenant, role):
        """Add user to tenant with role."""
        from apps.tenants.models import UserTenantRole

        return UserTenantRole.objects.create(
            user=user,
            tenant=tenant,
            role=role,
        )

    def test_select_tenant_success(self):
        """Test selecting a tenant user has access to."""
        tenant = self._create_tenant("Test Tenant", "test-tenant")
        self._add_user_to_tenant(self.user, tenant, "MEMBER")

        data = {"tenant_id": str(tenant.id)}
        response = self.client.post(self.select_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_select_tenant_no_access(self):
        """Test selecting a tenant user doesn't have access to fails."""
        from apps.tenants.models import Tenant

        other_tenant = Tenant.objects.create(
            name="Other Tenant",
            slug="other-tenant",
        )

        data = {"tenant_id": str(other_tenant.id)}
        response = self.client.post(self.select_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
