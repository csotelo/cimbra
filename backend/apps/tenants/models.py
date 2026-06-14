"""Tenant model definition."""

import uuid

from django.db import models
from django.utils.text import slugify


class Tenant(models.Model):
    """Represents an isolated workspace within the multi-tenant system.

    Each tenant has its own data namespace but shares the same database.
    Tenants can be enabled/disabled and have configurable limits.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    name = models.CharField(max_length=255)

    slug = models.SlugField(max_length=100, unique=True)

    is_active = models.BooleanField(default=True)

    max_users = models.PositiveIntegerField(default=10)

    rate_limit = models.PositiveIntegerField(
        default=100,
        help_text="API requests per minute",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tenants"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        base = slugify(self.name)
        slug = base
        counter = 1
        while Tenant.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base}-{counter}"
            counter += 1
        self.slug = slug
        super().save(*args, **kwargs)

    def can_add_user(self):
        """Check if tenant can accept more users."""
        return self.member_roles.count() < self.max_users

    def add_owner(self, user):
        """Assign user as owner of this tenant."""
        return UserTenantRole.objects.create(
            user=user,
            tenant=self,
            role=UserTenantRole.Role.OWNER,
        )

    def deactivate(self):
        """Soft delete — mark tenant as inactive."""
        self.is_active = False
        self.save(update_fields=["is_active"])


class UserTenantRole(models.Model):
    """M2M relationship between CustomUser and Tenant with role assignment.

    A user can have different roles in different tenants.
    This allows flexible permission management per tenant.
    """

    class Role(models.TextChoices):
        OWNER = "OWNER", "Owner"
        ADMIN = "ADMIN", "Admin"
        MEMBER = "MEMBER", "Member"

    user = models.ForeignKey(
        "users.CustomUser",
        on_delete=models.CASCADE,
        related_name="tenant_roles",
    )

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="member_roles",
    )

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.MEMBER,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_tenant_roles"
        unique_together = ["user", "tenant"]

    def __str__(self):
        return f"{self.user.email} - {self.tenant.name} ({self.role})"
