import json

from celery.result import AsyncResult
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.jobs.models import UserTask
from apps.jobs.tasks import sample_task


def user_tasks_queryset(user):
    """Return UserTask queryset visible to the user.

    SuperAdmin sees all registered tasks.
    Regular users see only their own.
    """
    if user.is_superuser:
        return UserTask.objects.all()
    return UserTask.objects.filter(user=user)


def enrich_with_redis(user_task):
    """Read live task state from Redis via AsyncResult."""
    result = AsyncResult(user_task.task_id)
    data = {
        "task_id": user_task.task_id,
        "task_name": user_task.task_name,
        "status": result.state,
        "result": None,
        "traceback": None,
        "date_created": user_task.created_at.isoformat(),
        "date_done": None,
        "duration_seconds": None,
        "worker": None,
    }
    if result.state == "SUCCESS" and result.result is not None:
        try:
            data["result"] = json.dumps(result.result)
        except (TypeError, ValueError):
            data["result"] = str(result.result)
    elif result.state == "FAILURE":
        data["traceback"] = str(result.traceback)
    return data


class DispatchJobView(APIView):
    """POST /api/jobs/dispatch/ — boilerplate pattern 2 reference endpoint."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        message = request.data.get("message", "test")
        task = sample_task.delay(user_id=request.user.id, message=message)
        UserTask.register(user=request.user, task=task, task_name="apps.jobs.tasks.sample_task")
        return Response({"task_id": str(task.id), "status": "dispatched"}, status=status.HTTP_202_ACCEPTED)


class JobListView(APIView):
    """GET /api/jobs/ — lista paginada de jobs del usuario autenticado.

    Fuente de verdad: UserTask (PostgreSQL) para propiedad,
    AsyncResult (Redis) para estado en vivo.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = user_tasks_queryset(request.user).order_by("-created_at")

        search = request.query_params.get("search")
        if search:
            qs = qs.filter(task_name__icontains=search)

        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(qs, request)

        jobs = [enrich_with_redis(ut) for ut in page]

        status_filter = request.query_params.get("status", "").upper()
        if status_filter:
            jobs = [j for j in jobs if j["status"] == status_filter]

        return paginator.get_paginated_response(jobs)


class JobDetailView(APIView):
    """GET /api/jobs/<task_id>/ — detalle de un job propio."""

    permission_classes = [IsAuthenticated]

    def get(self, request, task_id):
        try:
            ut = user_tasks_queryset(request.user).get(task_id=task_id)
        except UserTask.DoesNotExist:
            return Response({"detail": "Job not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(enrich_with_redis(ut))

    def delete(self, request, task_id):
        try:
            ut = user_tasks_queryset(request.user).get(task_id=task_id)
        except UserTask.DoesNotExist:
            return Response({"detail": "Job not found."}, status=status.HTTP_404_NOT_FOUND)
        AsyncResult(task_id).forget()
        ut.delete()
        return Response({"detail": "Job deleted."}, status=status.HTTP_200_OK)
