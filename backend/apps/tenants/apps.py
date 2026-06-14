"""Tenants app configuration."""

from django.apps import AppConfig


class TenantsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.tenants"

    def ready(self):
        from django.contrib import admin
        from unfold.admin import ModelAdmin as UnfoldModelAdmin
        from apps.tenants.models import Tenant

        class TenantAdmin(UnfoldModelAdmin):
            list_display = [
                "name",
                "slug",
                "is_active",
                "member_count",
                "max_users",
                "created_at",
            ]
            list_filter = ["is_active", "created_at"]
            search_fields = ["name", "slug"]
            readonly_fields = ["id", "created_at", "updated_at"]
            fieldsets = [
                ("Basic Info", {"fields": ["id", "name", "slug", "is_active"]}),
                ("Limits", {"fields": ["max_users", "rate_limit"]}),
                ("Timestamps", {"fields": ["created_at", "updated_at"]}),
            ]

            def member_count(self, obj):
                return obj.member_roles.count()

            member_count.short_description = "Members"

        if Tenant not in admin.site._registry:
            admin.site.register(Tenant, TenantAdmin)
