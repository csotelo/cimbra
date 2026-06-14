"""Notification helpers — call from anywhere to push a notification."""

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from apps.notifications.models import Notification, NotificationType


def notify(users, notification_type: str, title: str, message: str, data: dict = None, action_url: str = None):
    """Create a Notification for each user and push it via WebSocket.

    Args:
        users: iterable of User instances
        notification_type: one of NotificationType values
        title: short title
        message: full message text
        data: optional JSON payload
    """
    channel_layer = get_channel_layer()
    payload = data or {}
    if action_url:
        payload = {**payload, "action_url": action_url}
    for user in users:
        n = Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            data=payload,
        )
        async_to_sync(channel_layer.group_send)(
            f"notifications_user_{user.id}",
            {
                "type": "notification.send",
                "id": str(n.id),
                "notification_type": n.notification_type,
                "title": n.title,
                "message": n.message,
                "created_at": n.created_at.isoformat(),
            },
        )
