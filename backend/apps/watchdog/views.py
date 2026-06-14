"""Service health + watchdog command endpoints."""

import json
import os
import uuid

import httpx
import redis
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from django_celery_beat.models import IntervalSchedule, PeriodicTask

from apps.jobs.models import UserTask
from apps.notifications.models import NotificationType
from apps.notifications.utils import notify
from apps.watchdog.tasks import SCHEDULABLE_TASKS, health_check_task

STREAM_SERVICES = ["watchdog"]
HTTP_SERVICES = {
    "apiauth": "http://apiauth:8001/health",
}


class IsSuperAdmin(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.is_superuser


class ServiceHealthView(APIView):
    """Returns health status of all registered services — superadmin only.

    GET /api/watchdog/health/
    """

    permission_classes = [IsSuperAdmin]

    def get(self, request):
        r = redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379"), decode_responses=True)
        results = {}

        # Stream-based services — check last_seen key in Redis
        for service in STREAM_SERVICES:
            raw = r.get(f"service:{service}:last_seen")
            if raw:
                results[service] = json.loads(raw)
            else:
                results[service] = {"service": service, "status": "down", "last_seen": None, "latency_ms": None}

        r.close()

        # HTTP services — direct health check
        for service, url in HTTP_SERVICES.items():
            try:
                resp = httpx.get(url, timeout=2.0)
                results[service] = {
                    "service": service,
                    "status": "ok" if resp.status_code == 200 else "error",
                    "latency_ms": int(resp.elapsed.total_seconds() * 1000),
                    "last_seen": None,
                }
            except Exception:
                results[service] = {"service": service, "status": "down", "latency_ms": None, "last_seen": None}

        overall = "ok" if all(s["status"] == "ok" for s in results.values()) else "degraded"
        return Response({"overall": overall, "services": results})


class DispatchInternalTaskView(APIView):
    """Dispatch an internal Celery task — boilerplate pattern 2.

    POST /api/watchdog/internal/dispatch/
    Launches health_check_task, registers UserTask → appears in Jobs list.
    """

    permission_classes = [IsSuperAdmin]

    def post(self, request):
        task = health_check_task.delay(user_id=request.user.id)
        UserTask.register(
            user=request.user,
            task=task,
            task_name="apps.watchdog.tasks.health_check_task",
        )
        return Response(
            {"task_id": str(task.id), "status": "dispatched"},
            status=status.HTTP_202_ACCEPTED,
        )


class WatchdogCommandView(APIView):
    """Send a remote command to the watchdog service — boilerplate pattern 3.

    POST /api/watchdog/watchdog/command/
    Body: {"action": "echo"|"system_info"|"ping", "payload": {...}}

    Watchdog reads from commands:watchdog stream, executes, writes result to Redis.
    Poll GET /api/watchdog/watchdog/command/{command_id}/ for the result.
    """

    permission_classes = [IsSuperAdmin]

    def post(self, request):
        action = request.data.get("action", "echo")
        payload = request.data.get("payload", {})
        command_id = str(uuid.uuid4())

        r = redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379"), decode_responses=True)
        r.xadd("commands:watchdog", {
            "command_id": command_id,
            "action": action,
            "payload": json.dumps(payload),
            "user_id": str(request.user.id),
        })
        r.close()

        return Response({
            "command_id": command_id,
            "action": action,
            "status": "sent",
            "poll": f"/api/watchdog/command/{command_id}/",
        }, status=202)


class WatchdogResultView(APIView):
    """Poll the result of a watchdog command — boilerplate pattern 3.

    GET /api/watchdog/watchdog/command/{command_id}/
    """

    permission_classes = [IsSuperAdmin]

    def get(self, request, command_id):
        r = redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379"), decode_responses=True)
        raw = r.get(f"result:watchdog:{command_id}")
        r.close()

        if not raw:
            return Response({"command_id": command_id, "status": "pending"}, status=202)

        return Response(json.loads(raw))


# ── User Schedules ─────────────────────────────────────────────────────────────

PERIOD_CHOICES = {
    "seconds": IntervalSchedule.SECONDS,
    "minutes": IntervalSchedule.MINUTES,
    "hours": IntervalSchedule.HOURS,
    "days": IntervalSchedule.DAYS,
}


def _user_schedule_name(user_id: int, task_key: str) -> str:
    return f"user_{user_id}_{task_key}"


def _serialize_schedule(pt: PeriodicTask, user_id: int) -> dict:
    interval = pt.interval
    return {
        "id": pt.id,
        "task_key": pt.name.split(f"user_{user_id}_", 1)[-1],
        "task": pt.task,
        "label": next(
            (v["label"] for v in SCHEDULABLE_TASKS.values() if v["task"] == pt.task),
            pt.task.split(".")[-1],
        ),
        "every": interval.every if interval else None,
        "period": interval.period if interval else None,
        "enabled": pt.enabled,
        "last_run_at": pt.last_run_at.isoformat() if pt.last_run_at else None,
        "total_run_count": pt.total_run_count,
    }


class ScheduleListView(APIView):
    """
    GET  /api/watchdog/schedules/         — list user's scheduled tasks
    POST /api/watchdog/schedules/         — create a new scheduled task
    GET  /api/watchdog/schedules/tasks/   — list available tasks to schedule
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        prefix = f"user_{request.user.id}_"
        schedules = PeriodicTask.objects.filter(name__startswith=prefix).select_related("interval")
        return Response([_serialize_schedule(s, request.user.id) for s in schedules])

    def post(self, request):
        task_key = request.data.get("task_key")
        every = request.data.get("every")
        period = request.data.get("period", "minutes")

        if task_key not in SCHEDULABLE_TASKS:
            return Response({"detail": f"Task '{task_key}' not available."}, status=400)
        if not every or not str(every).isdigit() or int(every) < 1:
            return Response({"detail": "'every' must be a positive integer."}, status=400)
        if period not in PERIOD_CHOICES:
            return Response({"detail": f"'period' must be one of: {list(PERIOD_CHOICES)}"}, status=400)

        name = _user_schedule_name(request.user.id, task_key)
        if PeriodicTask.objects.filter(name=name).exists():
            return Response({"detail": "Ya tienes una tarea programada de este tipo."}, status=400)

        interval, _ = IntervalSchedule.objects.get_or_create(
            every=int(every),
            period=PERIOD_CHOICES[period],
        )
        task_def = SCHEDULABLE_TASKS[task_key]
        pt = PeriodicTask.objects.create(
            name=name,
            task=task_def["task"],
            interval=interval,
            kwargs=json.dumps({"user_id": request.user.id}),
            enabled=True,
        )
        notify(
            users=[request.user],
            notification_type=NotificationType.SYSTEM_ALERT,
            title="Tarea programada creada",
            message=f"'{task_def['label']}' se ejecutará cada {every} {period}.",
            action_url="/watchdog",
        )
        return Response(_serialize_schedule(pt, request.user.id), status=201)


class ScheduleDetailView(APIView):
    """
    PATCH  /api/watchdog/schedules/<id>/  — update frequency or enabled
    DELETE /api/watchdog/schedules/<id>/  — remove schedule
    """

    permission_classes = [IsAuthenticated]

    def _get_schedule(self, request, pk):
        prefix = f"user_{request.user.id}_"
        try:
            return PeriodicTask.objects.select_related("interval").get(
                id=pk, name__startswith=prefix
            )
        except PeriodicTask.DoesNotExist:
            return None

    def patch(self, request, pk):
        pt = self._get_schedule(request, pk)
        if not pt:
            return Response({"detail": "Not found."}, status=404)

        every = request.data.get("every")
        period = request.data.get("period")
        enabled = request.data.get("enabled")

        if every is not None or period is not None:
            every = int(every or pt.interval.every)
            period_key = period or pt.interval.period
            if period_key not in PERIOD_CHOICES:
                return Response({"detail": "Invalid period."}, status=400)
            interval, _ = IntervalSchedule.objects.get_or_create(
                every=every,
                period=PERIOD_CHOICES[period_key],
            )
            pt.interval = interval

        changed_enabled = enabled is not None and bool(enabled) != pt.enabled
        if enabled is not None:
            pt.enabled = bool(enabled)

        pt.save()

        if changed_enabled:
            state = "activada" if pt.enabled else "pausada"
            task_label = next(
                (v["label"] for v in SCHEDULABLE_TASKS.values() if v["task"] == pt.task),
                pt.task.split(".")[-1],
            )
            notify(
                users=[request.user],
                notification_type=NotificationType.SYSTEM_ALERT,
                title=f"Tarea {state}",
                message=f"'{task_label}' ha sido {state}.",
                action_url="/watchdog",
            )

        return Response(_serialize_schedule(pt, request.user.id))

    def delete(self, request, pk):
        pt = self._get_schedule(request, pk)
        if not pt:
            return Response({"detail": "Not found."}, status=404)
        pt.delete()
        return Response(status=204)


class SchedulableTasksView(APIView):
    """GET /api/watchdog/schedules/tasks/ — catalog of tasks available to schedule."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response([
            {"key": k, "label": v["label"], "description": v["description"]}
            for k, v in SCHEDULABLE_TASKS.items()
        ])
