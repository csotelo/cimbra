"""UserTask — associates a Celery task_id with the user who triggered it."""

import uuid

from django.conf import settings
from django.db import models


class UserTask(models.Model):
    """Links a dispatched Celery task to the user who triggered it.

    Created at dispatch time. Used to filter JobListView by owner.
    SuperAdmin bypasses this filter and sees all tasks.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="celery_tasks",
    )
    task_id = models.CharField(max_length=255, db_index=True)
    task_name = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "user_tasks"
        unique_together = [("user", "task_id")]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} → {self.task_name} ({self.task_id[:8]})"

    @classmethod
    def register(cls, user, task, task_name: str = ""):
        """Call after task.delay() to register ownership."""
        cls.objects.get_or_create(
            user=user,
            task_id=str(task.id),
            defaults={"task_name": task_name},
        )
