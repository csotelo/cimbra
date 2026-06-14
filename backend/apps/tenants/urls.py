"""Tenants URL Configuration."""

from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.api_tokens.views import TenantTokenView
from apps.tenants.views import TenantMemberViewSet, TenantViewSet

router = DefaultRouter()
router.register("", TenantViewSet, basename="tenant")

tenant_member_list = TenantMemberViewSet.as_view(
    {
        "get": "list",
        "post": "create",
    }
)

tenant_member_detail = TenantMemberViewSet.as_view(
    {
        "delete": "destroy",
    }
)

tenant_member_role = TenantMemberViewSet.as_view(
    {
        "patch": "change_role",
    }
)

urlpatterns = [
    path(
        "<uuid:tenant_id>/members/",
        tenant_member_list,
        name="tenant-members",
    ),
    path(
        "<uuid:tenant_id>/members/<int:user_id>/",
        tenant_member_detail,
        name="tenant-member-detail",
    ),
    path(
        "<uuid:tenant_id>/members/<int:user_id>/role/",
        tenant_member_role,
        name="tenant-member-role",
    ),
    path(
        "<uuid:tenant_id>/token/",
        TenantTokenView.as_view(),
        name="tenant-token",
    ),
]

urlpatterns += router.urls
