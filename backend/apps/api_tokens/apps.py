"""API Tokens app configuration."""

from django.apps import AppConfig


class ApiTokensConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.api_tokens"

    def ready(self):
        from django.contrib import admin
        from unfold.admin import ModelAdmin as UnfoldModelAdmin
        from apps.api_tokens.models import APIToken

        class APITokenAdmin(UnfoldModelAdmin):
            list_display = ["owner", "tenant", "is_active", "expires_at", "created_at"]
            list_filter = ["is_active", "created_at"]
            search_fields = ["owner__email", "tenant__name"]
            readonly_fields = ["created_at", "updated_at"]

        if APIToken not in admin.site._registry:
            admin.site.register(APIToken, APITokenAdmin)
