"""Django Admin configuration using Unfold."""

from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(UnfoldModelAdmin):
    """Admin for Notification model."""

    list_display = [
        "notification_type",
        "title",
        "user",
        "is_read",
        "created_at",
    ]
    list_filter = ["notification_type", "is_read", "created_at"]
    search_fields = ["user__email", "title", "message"]
    readonly_fields = ["id", "created_at"]
    ordering = ["-created_at"]

    fieldsets = [
        (
            None,
            {
                "fields": [
                    "id",
                    "user",
                    "notification_type",
                    "title",
                    "message",
                ]
            },
        ),
        (
            "Status",
            {
                "fields": ["is_read", "data", "created_at"],
            },
        ),
    ]
