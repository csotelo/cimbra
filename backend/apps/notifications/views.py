"""Notification API views."""

from datetime import timedelta

from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications.models import Notification

READ_MAX_DAYS = 7
READ_MAX_COUNT = 20


def _serialize(n):
    return {
        "id": str(n.id),
        "type": n.notification_type,
        "title": n.title,
        "message": n.message,
        "is_read": n.is_read,
        "action_url": n.data.get("action_url") if n.data else None,
        "created_at": n.created_at.isoformat(),
    }


class NotificationListView(APIView):
    """GET /api/notifications/
    Returns: all unread + read from last 7 days (max 20 read), newest first.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        unread = list(
            Notification.objects.filter(user=request.user, is_read=False)
            .order_by("-created_at")
        )
        cutoff = timezone.now() - timedelta(days=READ_MAX_DAYS)
        read = list(
            Notification.objects.filter(user=request.user, is_read=True, created_at__gte=cutoff)
            .order_by("-created_at")[:READ_MAX_COUNT]
        )
        return Response([_serialize(n) for n in unread + read])


class NotificationUnreadCountView(APIView):
    """GET /api/notifications/unread/"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({"count": count})


class NotificationMarkReadView(APIView):
    """POST /api/notifications/read-all/"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({"status": "ok"})


class NotificationClearReadView(APIView):
    """DELETE /api/notifications/clear-read/ — delete all read notifications."""

    permission_classes = [IsAuthenticated]

    def delete(self, request):
        deleted, _ = Notification.objects.filter(user=request.user, is_read=True).delete()
        return Response({"deleted": deleted})


class NotificationDetailView(APIView):
    """PATCH /api/notifications/<id>/read/"""

    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            n = Notification.objects.get(id=pk, user=request.user)
            n.is_read = True
            n.save(update_fields=["is_read"])
            return Response({"status": "ok"})
        except Notification.DoesNotExist:
            return Response({"detail": "Not found."}, status=404)
