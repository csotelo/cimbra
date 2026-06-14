"""Users app configuration."""

from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.users"

    def ready(self):
        import apps.users.signals  # noqa: F401

        from django.contrib import admin
        from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
        from unfold.admin import ModelAdmin as UnfoldModelAdmin
        from apps.users.models import CustomUser
        from apps.tenants.models import UserTenantRole

        class UserTenantRoleInline(admin.TabularInline):
            model = UserTenantRole
            extra = 0
            readonly_fields = ["created_at", "updated_at"]

        class CustomUserAdmin(BaseUserAdmin, UnfoldModelAdmin):
            list_display = [
                "email",
                "is_email_verified",
                "is_active",
                "tenant_roles_count",
                "date_joined",
            ]
            list_filter = ["is_email_verified", "is_active", "date_joined"]
            search_fields = ["email"]
            readonly_fields = ["date_joined", "last_login"]
            filter_horizontal = []
            ordering = ["email"]
            fieldsets = (
                (None, {"fields": ("email", "password")}),
                (
                    "Status",
                    {"fields": ("is_active", "is_email_verified", "is_superuser")},
                ),
                (
                    "Tokens",
                    {
                        "fields": (
                            "email_verification_token",
                            "email_verification_token_expires",
                            "password_reset_token",
                            "password_reset_token_expires",
                        )
                    },
                ),
                ("Dates", {"fields": ("date_joined", "last_login")}),
            )
            inlines = [UserTenantRoleInline]

            def tenant_roles_count(self, obj):
                return obj.tenant_roles.count()

            tenant_roles_count.short_description = "Tenants"

        if CustomUser not in admin.site._registry:
            admin.site.register(CustomUser, CustomUserAdmin)
