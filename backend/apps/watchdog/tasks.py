"""Celery tasks for inter-service communication."""

import json
import os
import time
import uuid

import redis
from celery import shared_task

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

# Registry of tasks the user can schedule from the UI
SCHEDULABLE_TASKS = {
    "health_check": {
        "task": "apps.watchdog.tasks.health_check_task",
        "label": "Verificación de salud",
        "description": "Verifica conectividad interna con Redis",
    },
    "ping": {
        "task": "apps.watchdog.tasks.scheduled_ping",
        "label": "Ping al agente",
        "description": "Verifica conectividad de red desde el agente watchdog",
    },
    "echo": {
        "task": "apps.watchdog.tasks.scheduled_echo",
        "label": "Echo",
        "description": "Prueba de comunicación con el agente watchdog",
    },
}


def _self_register(task_id: str, user_id: int, task_name: str):
    """Register the running task as UserTask so it appears in Jobs."""
    from django.contrib.auth import get_user_model
    from apps.jobs.models import UserTask
    User = get_user_model()
    try:
        user = User.objects.get(id=user_id)
        UserTask.objects.get_or_create(
            user=user,
            task_id=task_id,
            defaults={"task_name": task_name},
        )
    except User.DoesNotExist:
        pass


def _send_watchdog_command(action: str, payload: dict, user_id: int) -> dict:
    """Send command to watchdog via Redis Stream and poll for result."""
    command_id = str(uuid.uuid4())
    r = redis.from_url(REDIS_URL, decode_responses=True)
    r.xadd("commands:watchdog", {
        "command_id": command_id,
        "action": action,
        "payload": json.dumps(payload),
        "user_id": str(user_id),
    })
    # Poll for result — watchdog processes in ~100ms
    for _ in range(20):
        time.sleep(0.5)
        raw = r.get(f"result:watchdog:{command_id}")
        if raw:
            r.close()
            return json.loads(raw)
    r.close()
    return {"status": "timeout", "command_id": command_id}


@shared_task(name="apps.watchdog.tasks.send_heartbeat_ping")
def send_heartbeat_ping():
    """Publish a heartbeat ping to Redis Stream — consumed by watchdog."""
    r = redis.from_url(REDIS_URL, decode_responses=True)
    r.xadd("stream:heartbeat", {
        "ping_id": str(uuid.uuid4()),
        "sent_at": str(time.time()),
        "source": "django",
    })
    r.close()


@shared_task(bind=True, name="apps.watchdog.tasks.health_check_task")
def health_check_task(self, user_id: int):
    """Internal health check — pattern 2 (Celery task, schedulable by user)."""
    _self_register(self.request.id, user_id, self.name)
    r = redis.from_url(REDIS_URL, decode_responses=True)
    try:
        t0 = time.time()
        r.ping()
        latency_ms = int((time.time() - t0) * 1000)
        r.close()
        return {
            "status": "ok",
            "redis": "reachable",
            "latency_ms": latency_ms,
            "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
    except Exception as e:
        r.close()
        return {"status": "error", "error": str(e)}


@shared_task(bind=True, name="apps.watchdog.tasks.scheduled_ping")
def scheduled_ping(self, user_id: int, host: str = "redis"):
    """Scheduled ping — pattern 3 via Redis Stream, schedulable by user."""
    _self_register(self.request.id, user_id, self.name)
    return _send_watchdog_command("ping", {"host": host}, user_id)


@shared_task(bind=True, name="apps.watchdog.tasks.scheduled_echo")
def scheduled_echo(self, user_id: int, message: str = "hello"):
    """Scheduled echo — pattern 3 via Redis Stream, schedulable by user."""
    _self_register(self.request.id, user_id, self.name)
    return _send_watchdog_command("echo", {"message": message}, user_id)
