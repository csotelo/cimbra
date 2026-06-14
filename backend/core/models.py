"""Core models including BaseModel and TenantAwareManager."""

import uuid

from django.db import models

from core.middleware import get_current_tenant


class TenantAwareManager(models.Manager):
    """Manager that automatically filters queries by current tenant.

    Uses threading.local context to get the current tenant.
    Superusers bypass tenant filtering (SuperAdmin).
    """

    def get_queryset(self):
        """Return queryset filtered by current tenant context."""
        queryset = super().get_queryset()
        tenant = get_current_tenant()
        if tenant is not None:
            return queryset.filter(tenant_id=tenant.id)
        return queryset

    def for_tenant(self, tenant):
        """Return all objects for a specific tenant (bypass context)."""
        return super().get_queryset().filter(tenant_id=tenant.id)

    def all_tenants(self):
        """Return all objects ignoring tenant filter (for SuperAdmin)."""
        return super().get_queryset()


class BaseModel(models.Model):
    """Abstract base model for all tenant-aware models.

    Provides:
    - UUID primary key
    - Tenant foreign key
    - Timestamps
    - Soft delete via is_active flag

    Subclasses automatically use TenantAwareManager.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="%(class)s_set",
        null=False,
        blank=False,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    is_active = models.BooleanField(default=True)

    objects = TenantAwareManager()

    class Meta:
        abstract = True

    def __str__(self):
        return str(self.id)
