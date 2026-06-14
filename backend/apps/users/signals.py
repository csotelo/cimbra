"""User signals — auto-join to main tenant in SINGLE_TENANT_MODE."""

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender="users.CustomUser")
def auto_join_main_tenant(sender, instance, created, **kwargs):
    """Add new user to the main tenant as MEMBER when SINGLE_TENANT_MODE is True."""
    if not created:
        return
    if not getattr(settings, "SINGLE_TENANT_MODE", False):
        return

    slug = getattr(settings, "MAIN_TENANT_SLUG", "ximbra")

    from apps.tenants.models import Tenant, UserTenantRole

    try:
        tenant = Tenant.objects.get(slug=slug, is_active=True)
    except Tenant.DoesNotExist:
        return

    UserTenantRole.objects.get_or_create(
        user=instance,
        tenant=tenant,
        defaults={"role": UserTenantRole.Role.MEMBER},
    )
