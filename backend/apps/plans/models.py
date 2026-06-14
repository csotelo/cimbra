"""Plans and subscription models."""

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class Plan(models.Model):
    """Subscription plan defining user account limits.

    Plans are global — defined by superadmin, assigned to users.
    Limits apply to the user's entire account across all their tenants.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(
        default=False,
        help_text="Auto-assigned to new users on registration.",
    )

    max_tenants = models.PositiveIntegerField(
        default=1,
        help_text="Maximum number of tenants the user can own.",
    )
    rate_limit_per_minute = models.PositiveIntegerField(
        default=60,
        help_text="Max API requests per minute (enforcement via Redis).",
    )
    requests_per_hour = models.PositiveIntegerField(
        default=1_000,
        help_text="Max API requests per hour (quota).",
    )
    requests_per_day = models.PositiveIntegerField(
        default=10_000,
        help_text="Max API requests per day (quota).",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "plans"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Only one plan can be the default
        if self.is_default:
            Plan.objects.exclude(pk=self.pk).filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)


class UserSubscription(models.Model):
    """Records a user's subscription to a plan.

    Only one active subscription per user (valid_to IS NULL).
    Every plan change creates a new record — old one gets valid_to set.
    This preserves full history for billing and auditing.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscriptions",
    )
    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name="subscriptions",
    )
    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField(
        null=True,
        blank=True,
        help_text="NULL means currently active.",
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="plan_changes_made",
        help_text="Admin who made the change.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "user_subscriptions"
        ordering = ["-valid_from"]
        indexes = [
            models.Index(fields=["user", "valid_to"]),
        ]

    def __str__(self):
        status = "active" if self.valid_to is None else "closed"
        return f"{self.user.email} → {self.plan.name} ({status})"

    @classmethod
    def get_active(cls, user):
        """Return the user's current active subscription or None."""
        return cls.objects.filter(user=user, valid_to__isnull=True).select_related("plan").first()

    @classmethod
    def assign_plan(cls, user, plan, changed_by=None):
        """Assign a plan to a user, closing the previous subscription.

        Invalidates the Redis plan cache so apiauth picks up the new limits
        on the next request — critical for downgrades and suspensions.
        """
        now = timezone.now()
        cls.objects.filter(user=user, valid_to__isnull=True).update(valid_to=now)
        result = cls.objects.create(user=user, plan=plan, valid_from=now, changed_by=changed_by)
        cls._invalidate_plan_cache(user.id)
        return result

    @staticmethod
    def _invalidate_plan_cache(user_id):
        """Delete plan cache entry from Redis (same DB as apiauth)."""
        try:
            import os
            import redis
            r = redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379"), decode_responses=True)
            r.delete(f"plan:{user_id}")
            r.close()
        except Exception:
            pass  # Cache miss is acceptable; apiauth will re-read from DB
