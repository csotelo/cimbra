"""Django Admin configuration using Unfold."""

from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin

from apps.tenants.models import Tenant, UserTenantRole


class UserTenantRoleInline(UnfoldModelAdmin):
    """Inline admin for user tenant roles."""

    model = UserTenantRole
    extra = 0
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Tenant)
class TenantAdmin(UnfoldModelAdmin):
    """Admin configuration for Tenant model."""

    list_display = [
        "name",
        "slug",
        "is_active",
        "member_count",
        "max_users",
        "created_at",
    ]

    list_filter = [
        "is_active",
        "created_at",
    ]

    search_fields = [
        "name",
        "slug",
    ]

    readonly_fields = [
        "id",
        "slug",
        "created_at",
        "updated_at",
    ]

    fieldsets = [
        (
            "Basic Info",
            {
                "fields": [
                    "id",
                    "name",
                    "slug",
                    "is_active",
                ]
            },
        ),
        (
            "Limits",
            {
                "fields": [
                    "max_users",
                    "rate_limit",
                ]
            },
        ),
        (
            "Timestamps",
            {
                "fields": [
                    "created_at",
                    "updated_at",
                ]
            },
        ),
    ]

    def member_count(self, obj):
        """Display member count."""
        return obj.member_roles.count()

    member_count.short_description = "Members"

    def save_model(self, request, obj, form, change):
        is_new = not change
        super().save_model(request, obj, form, change)
        if is_new:
            obj.add_owner(request.user)
