"""Views for tenant CRUD and member management."""

from django.contrib.auth import get_user_model
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.tenants.models import Tenant, UserTenantRole
from apps.tenants.permissions import TenantAwareViewMixin
from apps.tenants.serializers import (
    AddMemberSerializer,
    ChangeMemberRoleSerializer,
    TenantMemberSerializer,
    TenantSerializer,
    TenantUpdateSerializer,
)
from core.middleware import set_current_tenant

User = get_user_model()


def is_superadmin(user):
    if user and getattr(user, "is_authenticated", False):
        return getattr(user, "is_superuser", False)
    return False


ADMIN_OR_OWNER_ROLES = [
    UserTenantRole.Role.OWNER,
    UserTenantRole.Role.ADMIN,
]


class TenantViewSet(TenantAwareViewMixin, viewsets.ModelViewSet):
    """ViewSet for tenant CRUD operations.

    POST /api/tenants/ - Create tenant (becomes owner automatically)
    GET /api/tenants/ - List user's tenants (UserScope)
    GET /api/tenants/{id}/ - Get tenant detail
    PATCH /api/tenants/{id}/ - Update tenant (owner only)
    DELETE /api/tenants/{id}/ - Soft delete tenant (owner only)
    """

    permission_classes = [IsAuthenticated]
    search_fields = ["name", "slug"]
    ordering_fields = ["name", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            qs = Tenant.objects.all()
        else:
            qs = Tenant.objects.filter(member_roles__user=user)

        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == "true")

        return qs

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "partial_update":
            return TenantUpdateSerializer
        return TenantSerializer

    def create(self, request):
        """Create a new tenant.

        User automatically becomes owner of the created tenant.
        Enforces max_tenants limit from the user's active plan.
        """
        if not is_superadmin(request.user):
            from apps.plans.models import UserSubscription

            sub = UserSubscription.get_active(request.user)
            if sub:
                owned = Tenant.objects.filter(
                    member_roles__user=request.user,
                    member_roles__role=UserTenantRole.Role.OWNER,
                    is_active=True,
                ).count()
                if owned >= sub.plan.max_tenants:
                    return Response(
                        {
                            "detail": (
                                f"Tu plan '{sub.plan.name}' permite máximo "
                                f"{sub.plan.max_tenants} tenant(s). "
                                "Actualiza tu plan para crear más."
                            )
                        },
                        status=status.HTTP_403_FORBIDDEN,
                    )

        serializer = TenantSerializer(
            data=request.data,
            context={"request": request},
        )
        if serializer.is_valid():
            tenant = serializer.save()
            set_current_tenant(tenant)
            return Response(
                TenantSerializer(tenant, context={"request": request}).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, pk=None):
        """Update tenant (owner only).

        Only owner can update tenant settings.
        """
        tenant = self.get_object()

        if not is_superadmin(request.user) and not request.user.is_owner_of(tenant):
            return Response(
                {"detail": "Only owner can update tenant."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = TenantUpdateSerializer(
            tenant,
            data=request.data,
            partial=True,
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                TenantSerializer(tenant, context={"request": request}).data,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        """Soft delete tenant (owner only).

        Sets is_active=False instead of deleting.
        """
        tenant = self.get_object()

        if not is_superadmin(request.user) and not request.user.is_owner_of(tenant):
            return Response(
                {"detail": "Only owner can delete tenant."},
                status=status.HTTP_403_FORBIDDEN,
            )

        tenant.deactivate()
        return Response({"detail": "Tenant deactivated."}, status=status.HTTP_200_OK)


class TenantMemberViewSet(TenantAwareViewMixin, viewsets.ViewSet):
    """ViewSet for tenant member management.

    GET /api/tenants/{tenant_id}/members/ - List members
    POST /api/tenants/{tenant_id}/members/ - Add member (admin+)
    DELETE /api/tenants/{tenant_id}/members/{user_id}/ - Remove member
    PATCH /api/tenants/{tenant_id}/members/{user_id}/role/ - Change role
    """

    permission_classes = [IsAuthenticated]

    def get_tenant(self, tenant_id):
        """Get tenant and verify access."""
        try:
            tenant = Tenant.objects.get(id=tenant_id)
        except Tenant.DoesNotExist:
            return None

        if is_superadmin(self.request.user):
            return tenant

        has_access = UserTenantRole.objects.filter(
            user=self.request.user,
            tenant=tenant,
        ).exists()

        if not has_access:
            return None

        return tenant

    def list(self, request, tenant_id=None):
        """List all members of a tenant.

        Returns member list with roles.
        """
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return Response(
                {"detail": "Tenant not found or access denied."},
                status=status.HTTP_404_NOT_FOUND,
            )

        members = UserTenantRole.objects.filter(
            tenant=tenant,
        ).select_related("user")

        serializer = TenantMemberSerializer(members, many=True)
        return Response(serializer.data)

    def create(self, request, tenant_id=None):
        """Add a member to tenant.

        Requires admin or owner role.
        Enforces tenant max_users limit.
        """
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return Response(
                {"detail": "Tenant not found or access denied."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not tenant.is_active:
            return Response(
                {"detail": "Tenant is not active."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not is_superadmin(request.user) and not request.user.has_role_in_tenant(tenant):
            return Response(
                {"detail": "Only admin or owner can add members."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = AddMemberSerializer(
            data=request.data,
            context={"request": request, "tenant": tenant},
        )

        if serializer.is_valid():
            membership = serializer.save()
            return Response(
                TenantMemberSerializer(membership).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, tenant_id=None, user_id=None):
        """Remove a member from tenant.

        Requires admin or owner role.
        Cannot remove the owner.
        """
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return Response(
                {"detail": "Tenant not found or access denied."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not is_superadmin(request.user) and not request.user.has_role_in_tenant(tenant):
            return Response(
                {"detail": "Only admin or owner can remove members."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            target_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            membership = UserTenantRole.objects.get(
                user=target_user,
                tenant=tenant,
            )
        except UserTenantRole.DoesNotExist:
            return Response(
                {"detail": "User is not a member of this tenant."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if membership.role == UserTenantRole.Role.OWNER:
            return Response(
                {"detail": "Cannot remove the owner."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if target_user.id == request.user.id:
            return Response(
                {"detail": "Cannot remove yourself."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        membership.delete()

        return Response(
            {"detail": "Member removed."},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["patch"], url_path="role")
    def change_role(self, request, tenant_id=None, user_id=None):
        """Change a member's role.

        Only owner can change roles.
        Cannot change owner's role.
        Cannot change your own role.
        """
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return Response(
                {"detail": "Tenant not found or access denied."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not is_superadmin(request.user) and not request.user.is_owner_of(tenant):
            return Response(
                {"detail": "Only owner can change roles."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            target_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ChangeMemberRoleSerializer(
            data=request.data,
            context={
                "request": request,
                "user": target_user,
                "tenant": tenant,
            },
        )

        if serializer.is_valid():
            membership = UserTenantRole.objects.get(
                user=target_user,
                tenant=tenant,
            )
            membership.role = serializer.validated_data["role"]
            membership.save()

            return Response(
                TenantMemberSerializer(membership).data,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
