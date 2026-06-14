"""Views for API token management."""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api_tokens.models import APIToken
from apps.api_tokens.serializers import (
    APITokenCreateSerializer,
    APITokenStatusSerializer,
)
from apps.tenants.models import Tenant, UserTenantRole


def is_superadmin(user):
    """Check if user is superadmin."""
    if user and getattr(user, "is_authenticated", False):
        return getattr(user, "is_superuser", False)
    return False


def user_is_owner(user, tenant):
    """Check if user is owner of the tenant."""
    if is_superadmin(user):
        return True
    return UserTenantRole.objects.filter(
        user=user,
        tenant=tenant,
        role=UserTenantRole.Role.OWNER,
    ).exists()


class TenantTokenView(APIView):
    """View for managing tenant API tokens.

    POST /api/tenants/{tenant_id}/token/ - Generate new token
    GET /api/tenants/{tenant_id}/token/ - View token status
    DELETE /api/tenants/{tenant_id}/token/ - Revoke token
    """

    permission_classes = [IsAuthenticated]

    def get_tenant(self, tenant_id, user):
        """Get tenant and verify ownership."""
        try:
            tenant = Tenant.objects.get(id=tenant_id)
        except Tenant.DoesNotExist:
            return None

        if not tenant.is_active:
            return None

        if not user_is_owner(user, tenant):
            return None

        return tenant

    def get(self, request, tenant_id):
        """Get token status for tenant.

        Returns token info without exposing the actual token value.
        """
        tenant = self.get_tenant(tenant_id, request.user)
        if not tenant:
            return Response(
                {"detail": "Tenant not found or access denied."},
                status=status.HTTP_404_NOT_FOUND,
            )

        token = APIToken.objects.filter(
            tenant=tenant,
            owner=request.user,
            is_active=True,
        ).first()

        if not token:
            return Response(
                {"detail": "No active token found for this tenant."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = APITokenStatusSerializer(token)
        return Response(serializer.data)

    def post(self, request, tenant_id):
        """Generate a new API token.

        Revokes any existing active token for this tenant.
        Returns the new token value (shown only once).
        """
        tenant = self.get_tenant(tenant_id, request.user)
        if not tenant:
            return Response(
                {"detail": "Tenant not found or access denied."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = APITokenCreateSerializer(
            data={},
            context={
                "request": request,
                "tenant": tenant,
                "owner": request.user,
            },
        )

        if serializer.is_valid():
            token_obj = serializer.save()
            response_data = {
                "token": token_obj.token,
                "tenant_id": str(tenant.id),
                "expires_at": token_obj.expires_at,
                "message": "Token generated. Save it now, it won't be shown again.",
            }
            return Response(response_data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, tenant_id):
        """Revoke the current API token."""
        tenant = self.get_tenant(tenant_id, request.user)
        if not tenant:
            return Response(
                {"detail": "Tenant not found or access denied."},
                status=status.HTTP_404_NOT_FOUND,
            )

        token = APIToken.objects.filter(
            tenant=tenant,
            owner=request.user,
            is_active=True,
        ).first()

        if not token:
            return Response(
                {"detail": "No active token to revoke."},
                status=status.HTTP_404_NOT_FOUND,
            )

        token.revoke()
        return Response(
            {"detail": "Token revoked successfully."},
            status=status.HTTP_200_OK,
        )
