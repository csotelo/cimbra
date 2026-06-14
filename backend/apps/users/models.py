"""CustomUser model with email-based authentication."""

import secrets
import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
from django.utils import timezone


class CustomUserManager(BaseUserManager):
    """Manager for CustomUser with email-based authentication."""

    def create_user(self, email, password=None, **extra_fields):
        """Create and return a regular user with email and password."""
        if not email:
            msg = "Users must have an email address"
            raise ValueError(msg)
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and return a superuser with email and password."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_email_verified", True)

        if extra_fields.get("is_staff") is not True:
            msg = "Superuser must have is_staff=True."
            raise ValueError(msg)
        if extra_fields.get("is_superuser") is not True:
            msg = "Superuser must have is_superuser=True."
            raise ValueError(msg)

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser):
    """Custom user model using email as unique identifier.

    This replaces Django's default username-based authentication.
    Users can belong to multiple tenants with different roles.
    """

    email = models.EmailField(
        unique=True,
        max_length=255,
    )

    is_email_verified = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)

    is_staff = models.BooleanField(default=False)

    is_superuser = models.BooleanField(default=False)

    date_joined = models.DateTimeField(auto_now_add=True)

    email_verification_token = models.CharField(
        max_length=64,
        blank=True,
        null=True,
    )

    email_verification_token_expires = models.DateTimeField(
        blank=True,
        null=True,
    )

    password_reset_token = models.CharField(
        max_length=64,
        blank=True,
        null=True,
    )

    password_reset_token_expires = models.DateTimeField(
        blank=True,
        null=True,
    )

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "custom_users"

    def __str__(self):
        return self.email

    def get_full_name(self):
        return self.email

    def get_short_name(self):
        return self.email.split("@")[0]

    def generate_email_verification_token(self):
        """Generate a unique email verification token."""
        self.email_verification_token = secrets.token_urlsafe(48)
        from django.utils import timezone
        from django.conf import settings

        expiry_hours = getattr(settings, "EMAIL_VERIFICATION_EXPIRY_HOURS", 24)
        self.email_verification_token_expires = timezone.now() + timezone.timedelta(
            hours=expiry_hours
        )
        self.save(
            update_fields=[
                "email_verification_token",
                "email_verification_token_expires",
            ]
        )
        return self.email_verification_token

    def generate_password_reset_token(self):
        """Generate a unique password reset token."""
        self.password_reset_token = secrets.token_urlsafe(48)
        from django.utils import timezone
        from django.conf import settings

        expiry_hours = getattr(settings, "PASSWORD_RESET_EXPIRY_HOURS", 1)
        self.password_reset_token_expires = timezone.now() + timezone.timedelta(
            hours=expiry_hours
        )
        self.save(
            update_fields=[
                "password_reset_token",
                "password_reset_token_expires",
            ]
        )
        return self.password_reset_token

    def clear_verification_token(self):
        """Clear email verification token after successful verification."""
        self.email_verification_token = None
        self.email_verification_token_expires = None
        self.save(
            update_fields=[
                "email_verification_token",
                "email_verification_token_expires",
            ]
        )

    def clear_password_reset_token(self):
        """Clear password reset token after successful reset."""
        self.password_reset_token = None
        self.password_reset_token_expires = None
        self.save(
            update_fields=["password_reset_token", "password_reset_token_expires"]
        )

    def _get_role_choices(self):
        """Get role constants to avoid circular import."""
        from apps.tenants.models import UserTenantRole

        return UserTenantRole.Role

    def has_role_in_tenant(self, tenant, role=None):
        """Check if user has a specific role (or any role) in tenant."""
        from apps.tenants.models import UserTenantRole

        qs = UserTenantRole.objects.filter(user=self, tenant=tenant)
        if role:
            qs = qs.filter(role=role)
        return qs.exists()

    def is_owner_of(self, tenant):
        """Check if user is owner of the given tenant."""
        role = self._get_role_choices()
        return self.has_role_in_tenant(tenant, role.OWNER)

    def is_admin_of(self, tenant):
        """Check if user is admin of the given tenant."""
        role = self._get_role_choices()
        return self.has_role_in_tenant(tenant, role.ADMIN)

    def is_member_of(self, tenant):
        """Check if user is member of the given tenant."""
        role = self._get_role_choices()
        return self.has_role_in_tenant(tenant, role.MEMBER)

    def can_create_tenant(self):
        """Check if user can create another tenant (MAX_TENANTS_PER_USER limit)."""
        from django.conf import settings
        from apps.tenants.models import UserTenantRole
        max_tenants = getattr(settings, "MAX_TENANTS_PER_USER", 5)
        owned = UserTenantRole.objects.filter(
            user=self,
            role=UserTenantRole.Role.OWNER,
            tenant__is_active=True,
        ).count()
        return owned < max_tenants

    def get_tenant_list(self):
        """Return list of active tenants with role for login response."""
        from apps.tenants.models import UserTenantRole
        roles = UserTenantRole.objects.filter(
            user=self,
            tenant__is_active=True,
        ).select_related("tenant")
        return [
            {
                "id": str(r.tenant.id),
                "name": r.tenant.name,
                "slug": r.tenant.slug,
                "role": r.role,
            }
            for r in roles
        ]

    def get_unread_notifications(self, limit=20):
        """Return unread notifications for login response."""
        qs = self.notifications.filter(is_read=False).order_by("-created_at")
        items = qs[:limit]
        return [
            {
                "id": str(n.id),
                "type": n.notification_type,
                "title": n.title,
                "message": n.message,
                "data": n.data,
                "created_at": n.created_at.isoformat(),
            }
            for n in items
        ], qs.count()

    def reset_password(self, new_password):
        """Set new password and clear reset token atomically."""
        self.set_password(new_password)
        self.password_reset_token = None
        self.password_reset_token_expires = None
        self.save(update_fields=[
            "password", "password_reset_token", "password_reset_token_expires"
        ])

    def has_module_perms(self, app_label):
        """Check if user has permissions for the given app."""
        return self.is_superuser or self.is_staff

    def has_perm(self, perm, obj=None):
        """Check if user has the given permission."""
        return self.is_superuser or self.is_staff


class Invitation(models.Model):
    """Email invitation to join the platform (and auto-join the main tenant)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField()
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    invited_by = models.ForeignKey(
        "users.CustomUser",
        on_delete=models.SET_NULL,
        null=True,
        related_name="sent_invitations",
    )
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "invitations"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Invitation({self.email}, {'accepted' if self.accepted_at else 'pending'})"

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(hours=72)
        super().save(*args, **kwargs)

    @property
    def is_valid(self):
        return self.accepted_at is None and timezone.now() < self.expires_at

    def accept(self):
        self.accepted_at = timezone.now()
        self.save(update_fields=["accepted_at"])
