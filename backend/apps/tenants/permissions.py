"""Permissions for tenant-scoped access control."""

from rest_framework.permissions import BasePermission

from apps.tenants.models import UserTenantRole
from core.middleware import get_current_tenant, get_current_user, get_is_superadmin


class IsTenantOwner(BasePermission):
    """Permission check for tenant owner role.

    Allows access only if user is the Owner of the current tenant.
    SuperAdmin bypasses this check.
    """

    def has_permission(self, request, view):
        """Check if user has owner permission on current tenant."""
        if get_is_superadmin():
            return True

        user = get_current_user()
        tenant = get_current_tenant()

        if not user or not tenant:
            return False

        return UserTenantRole.objects.filter(
            user=user,
            tenant=tenant,
            role=UserTenantRole.Role.OWNER,
        ).exists()


class IsTenantAdmin(BasePermission):
    """Permission check for tenant admin role.

    Allows access if user is Owner or Admin of the current tenant.
    SuperAdmin bypasses this check.
    """

    def has_permission(self, request, view):
        """Check if user has admin or owner permission on current tenant."""
        if get_is_superadmin():
            return True

        user = get_current_user()
        tenant = get_current_tenant()

        if not user or not tenant:
            return False

        return UserTenantRole.objects.filter(
            user=user,
            tenant=tenant,
            role__in=[UserTenantRole.Role.OWNER, UserTenantRole.Role.ADMIN],
        ).exists()


class IsTenantMember(BasePermission):
    """Permission check for any tenant member role.

    Allows access if user is Owner, Admin, or Member of the current tenant.
    SuperAdmin bypasses this check.
    """

    def has_permission(self, request, view):
        """Check if user is any member of current tenant."""
        if get_is_superadmin():
            return True

        user = get_current_user()
        tenant = get_current_tenant()

        if not user or not tenant:
            return False

        return UserTenantRole.objects.filter(
            user=user,
            tenant=tenant,
        ).exists()


def get_user_role_in_tenant(user, tenant):
    """Get user's role in a specific tenant.

    Args:
        user: User instance
        tenant: Tenant instance

    Returns:
        Role string or None if user is not a member
    """
    try:
        membership = UserTenantRole.objects.get(user=user, tenant=tenant)
        return membership.role
    except UserTenantRole.DoesNotExist:
        return None


def user_is_owner(user, tenant):
    """Check if user is owner of the tenant."""
    if get_is_superadmin():
        return True
    return get_user_role_in_tenant(user, tenant) == UserTenantRole.Role.OWNER


def user_is_admin_or_owner(user, tenant):
    """Check if user is admin or owner of the tenant."""
    if get_is_superadmin():
        return True
    role = get_user_role_in_tenant(user, tenant)
    return role in [UserTenantRole.Role.OWNER, UserTenantRole.Role.ADMIN]


def user_is_member(user, tenant):
    """Check if user is any member of the tenant."""
    if get_is_superadmin():
        return True
    return get_user_role_in_tenant(user, tenant) is not None


class TenantAwareViewMixin:
    """Mixin that injects tenant context into views.

    Sets the current tenant from the URL kwargs before processing the request.
    This ensures TenantMiddleware context is available for permission checks
    and TenantAwareManager filtering.
    """

    def get_tenant_from_request(self):
        """Extract tenant from URL kwargs or request data.

        Returns:
            Tenant instance or None if not found.
        """
        from apps.tenants.models import Tenant

        tenant_id = self.kwargs.get("tenant_id") or self.kwargs.get("pk")
        if not tenant_id:
            return None

        try:
            return Tenant.objects.get(id=tenant_id)
        except Tenant.DoesNotExist:
            return None

    def initial(self, request, *args, **kwargs):
        """Set tenant context before processing the request."""
        super().initial(request, *args, **kwargs)

        if request.user and request.user.is_authenticated:
            tenant = self.get_tenant_from_request()
            if tenant:
                from core.middleware import set_current_tenant, set_current_user

                set_current_user(request.user)
                set_current_tenant(tenant)
