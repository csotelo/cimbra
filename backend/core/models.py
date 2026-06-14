"""Core models including BaseModel, TenantAwareManager y SiteConfig."""

import uuid

from django.db import models

from core.middleware import get_current_tenant


class SiteConfig(models.Model):
    """Configuración global del sitio — singleton (siempre pk=1).

    Controla SEO (título, descripción, OG image, favicon), indexación por
    buscadores y color de marca (skin primario).
    """
    site_name = models.CharField(max_length=100, default="Ximbra")
    site_description = models.TextField(blank=True, default="")
    og_image_url = models.URLField(blank=True, default="",
                                   help_text="URL de imagen para Open Graph (redes sociales)")
    favicon_url = models.URLField(blank=True, default="",
                                  help_text="URL del favicon (.ico o .png)")
    allow_indexing = models.BooleanField(default=False,
                                         help_text="Permitir indexación por buscadores (robots.txt)")
    primary_color = models.CharField(max_length=7, default="#4f46e5",
                                     help_text="Color primario hex (#rrggbb) — skin del sistema")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "site_config"

    def __str__(self):
        return f"SiteConfig — {self.site_name}"

    @classmethod
    def get_solo(cls):
        """Retorna el único registro de configuración global, creándolo si no existe."""
        obj, _ = cls.objects.get_or_create(pk=1, defaults={"site_name": "Ximbra"})
        return obj


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
