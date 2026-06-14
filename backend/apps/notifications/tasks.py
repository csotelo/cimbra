"""Celery tasks for notifications."""

import json
import logging
from datetime import datetime, timezone

import redis
from celery import shared_task
from django.conf import settings

logger = logging.getLogger(__name__)

RATE_LIMIT_CHANNEL = "rate_limit_events"


@shared_task(bind=True, max_retries=3, retry_backoff=True)
def consume_rate_limit_events(self):
    """Consume rate limit events from Redis Pub/Sub.

    This task polls Redis for rate limit exceeded events published
    by FastAPI. When an event is received, it creates a notification
    in the database for the user.

    Uses a polling approach with a timeout so Celery can track
    task state and restart if needed.
    """
    redis_url = getattr(settings, "CELERY_BROKER_URL", "redis://redis:6379/0")
    redis_client = redis.from_url(redis_url, decode_responses=True)

    try:
        pubsub = redis_client.pubsub()
        pubsub.subscribe(RATE_LIMIT_CHANNEL)

        message = pubsub.get_message(ignore_subscribe_messages=True, timeout=5)
        if message and message["type"] == "message":
            try:
                data = json.loads(message["data"])
                process_rate_limit_event(data)
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON in message: {message['data']}")
            except Exception as e:
                logger.exception(f"Error processing message: {e}")

    except redis.ConnectionError:
        logger.error("Redis connection lost, retrying...")
        raise self.retry(countdown=5)
    finally:
        pubsub.close()
        redis_client.close()

    self.retry(countdown=1)


def process_rate_limit_event(data: dict):
    """Process a single rate limit event and create notification.

    Args:
        data: Event data containing user_id, tenant_id, endpoint,
              retry_after, and timestamp.
    """
    from apps.notifications.models import Notification, NotificationType

    user_id = data.get("user_id")
    tenant_id = data.get("tenant_id")
    endpoint = data.get("endpoint", "API")
    retry_after = data.get("retry_after", 60)

    if not user_id:
        logger.warning("Rate limit event missing user_id")
        return

    try:
        Notification.objects.create(
            user_id=user_id,
            notification_type=NotificationType.RATE_LIMIT_EXCEEDED,
            title="Rate Limit Exceeded",
            message=(
                f"You have exceeded the rate limit for {endpoint}. "
                f"Please retry after {retry_after} seconds."
            ),
            data={
                "tenant_id": str(tenant_id) if tenant_id else None,
                "endpoint": endpoint,
                "retry_after": retry_after,
                "timestamp": data.get(
                    "timestamp", datetime.now(timezone.utc).isoformat()
                ),
            },
        )
        logger.info(f"Created notification for user {user_id}")
    except Exception as e:
        logger.exception(f"Failed to create notification: {e}")
