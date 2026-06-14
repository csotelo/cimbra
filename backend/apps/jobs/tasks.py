"""User-dispatchable Celery tasks — boilerplate pattern 2."""

import time

from celery import shared_task


@shared_task(name="apps.jobs.tasks.sample_task", bind=True)
def sample_task(self, user_id: int, message: str = "test"):
    """Demo task — simulates work and returns a result.

    Boilerplate: shows how any user-triggered task integrates with UserTask
    so it appears in the user's own job list.
    """
    time.sleep(2)
    return {"user_id": user_id, "message": message, "status": "completed"}
