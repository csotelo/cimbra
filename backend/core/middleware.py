"""Middleware for tenant context injection via threading.local."""

import threading

from rest_framework_simplejwt.authentication import JWTAuthentication

_thread_locals = threading.local()


def get_current_tenant():
    """Get the current tenant from thread local storage.

    Returns:
        Tenant instance or None if no tenant context is set.
    """
    return getattr(_thread_locals, "tenant", None)


def get_current_user():
    """Get the current user from thread local storage.

    Returns:
        User instance or None if no user context is set.
    """
    return getattr(_thread_locals, "user", None)


def get_is_superadmin():
    """Check if current user is a SuperAdmin.

    Returns:
        True if user is authenticated and is_superuser is True.
    """
    user = get_current_user()
    return user is not None and getattr(user, "is_superuser", False)


def set_current_tenant(tenant):
    """Set the current tenant in thread local storage.

    Args:
        tenant: Tenant instance or None to clear context.
    """
    _thread_locals.tenant = tenant


def set_current_user(user):
    """Set the current user in thread local storage.

    Args:
        user: User instance or None to clear context.
    """
    _thread_locals.user = user


class TenantMiddleware:
    """Middleware that extracts tenant from request and sets context.

    Extracts tenant from:
    1. JWT token in Authorization header (preferred)
    2. X-Tenant-ID header (fallback for API clients)

    SuperAdmin users bypass tenant filtering (see TenantAwareManager).
    """

    def __init__(self, get_response):
        """Initialize middleware with response handler."""
        self.get_response = get_response
        self.jwt_auth = JWTAuthentication()

    def __call__(self, request):
        """Process request and set tenant context."""
        user = None
        tenant = None

        try:
            validated = self.jwt_auth.authenticate(request)
            if validated:
                user, _ = validated
        except Exception:
            pass

        if user is None:
            user = getattr(request, "user", None)

        if user and getattr(user, "is_authenticated", False):
            set_current_user(user)

            tenant_id = request.headers.get("X-Tenant-ID")
            if tenant_id and not user.is_superuser:
                tenant = self._get_tenant_from_id(tenant_id)
            elif not user.is_superuser:
                tenant = self._get_default_tenant(user)

        set_current_tenant(tenant)

        response = self.get_response(request)

        set_current_user(None)
        set_current_tenant(None)

        return response

    def _get_tenant_from_id(self, tenant_id):
        """Get tenant by ID if user has access to it."""
        from apps.tenants.models import UserTenantRole

        try:
            membership = UserTenantRole.objects.select_related("tenant").get(
                user=get_current_user(), tenant_id=tenant_id
            )
            return membership.tenant
        except UserTenantRole.DoesNotExist:
            return None

    def _get_default_tenant(self, user):
        """Get tenant for user — main tenant in SINGLE_TENANT_MODE, else first membership."""
        from django.conf import settings
        from apps.tenants.models import Tenant, UserTenantRole

        if getattr(settings, "SINGLE_TENANT_MODE", False):
            slug = getattr(settings, "MAIN_TENANT_SLUG", "ximbra")
            try:
                return Tenant.objects.get(slug=slug, is_active=True)
            except Tenant.DoesNotExist:
                return None

        try:
            membership = (
                UserTenantRole.objects.select_related("tenant")
                .filter(user=user)
                .first()
            )
            return membership.tenant if membership else None
        except Exception:
            return None
