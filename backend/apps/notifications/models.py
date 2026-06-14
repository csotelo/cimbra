"""Notification models for storing user alerts."""

import uuid

from django.conf import settings
from django.db import models


class NotificationType(models.TextChoices):
    """Notification type choices."""

    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded", "Rate Limit Exceeded"
    TENANT_INVITATION = "tenant_invitation", "Tenant Invitation"
    MEMBER_ROLE_CHANGED = "member_role_changed", "Member Role Changed"
    API_TOKEN_EXPIRING = "api_token_expiring", "API Token Expiring"
    SYSTEM_ALERT = "system_alert", "System Alert"


class Notification(models.Model):
    """Notification model for storing user alerts.

    Notifications are not tenant-aware since they are per-user.
    Users can have notifications from any tenant they belong to.
    """

    id = models.UUIDField(
        primary_key=True,
        editable=False,
        default=uuid.uuid4,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )

    notification_type = models.CharField(
        max_length=50,
        choices=NotificationType.choices,
        db_index=True,
    )

    title = models.CharField(max_length=255)

    message = models.TextField()

    is_read = models.BooleanField(default=False, db_index=True)

    data = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["user", "is_read", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.notification_type}: {self.title}"
