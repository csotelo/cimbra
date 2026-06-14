"""Dashboard widget registry models."""

import uuid

from django.conf import settings
from django.db import models


class Module(models.Model):
    """A registered application module that can provide widgets."""

    slug = models.CharField(max_length=100, unique=True)
    label = models.CharField(max_length=200)
    is_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "dashboard_modules"
        ordering = ["label"]

    def __str__(self):
        return self.label


class Widget(models.Model):
    """A widget offered by a module, available for placement on the dashboard."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="widgets")
    name = models.CharField(max_length=100)
    label = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    vue_component = models.CharField(max_length=100, help_text="Vue component name to render")
    default_visible = models.BooleanField(default=False)
    is_staff_only = models.BooleanField(default=False, help_text="Only superadmin can see this widget.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "dashboard_widgets"
        unique_together = [("module", "name")]
        ordering = ["module", "name"]

    def __str__(self):
        return f"{self.module.slug}::{self.name}"


class UserDashboard(models.Model):
    """Stores each user's widget preferences: visibility and position."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="dashboard_widgets",
    )
    widget = models.ForeignKey(Widget, on_delete=models.CASCADE, related_name="user_preferences")
    position = models.PositiveIntegerField(default=0)
    is_visible = models.BooleanField(default=True)

    class Meta:
        db_table = "dashboard_user_widgets"
        unique_together = [("user", "widget")]
        ordering = ["position"]

    def __str__(self):
        return f"{self.user.email} — {self.widget}"
