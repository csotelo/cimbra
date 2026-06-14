"""Django Admin configuration using Unfold."""

from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin

from apps.api_tokens.models import APIToken


@admin.register(APIToken)
class APITokenAdmin(UnfoldModelAdmin):
    """Admin configuration for APIToken model."""

    list_display = [
        "id",
        "tenant",
        "owner",
        "is_active",
        "is_expired_display",
        "last_used_at",
        "created_at",
    ]

    list_filter = [
        "is_active",
        "created_at",
    ]

    search_fields = [
        "tenant__name",
        "tenant__slug",
        "owner__email",
    ]

    readonly_fields = [
        "token",
        "created_at",
        "updated_at",
        "last_used_at",
        "is_expired_display",
    ]

    actions = ["revoke_tokens"]

    fieldsets = [
        (
            "Token Info",
            {
                "fields": [
                    "id",
                    "token",
                    "tenant",
                    "owner",
                    "is_active",
                ]
            },
        ),
        (
            "Timestamps",
            {
                "fields": [
                    "expires_at",
                    "last_used_at",
                    "created_at",
                    "updated_at",
                ]
            },
        ),
    ]

    def is_expired_display(self, obj):
        """Display expired status."""
        return obj.is_expired

    is_expired_display.boolean = True
    is_expired_display.short_description = "Expired"

    @admin.action(description="Revoke selected tokens")
    def revoke_tokens(self, request, queryset):
        """Bulk revoke selected tokens."""
        count = 0
        for token in queryset.filter(is_active=True):
            token.revoke()
            count += 1
        self.message_user(request, f"{count} token(s) revoked.")
