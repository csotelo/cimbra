"""Redis adapter for rate limiting and event publishing.

This adapter handles:
1. Rate limiting using sliding window algorithm
2. Event publishing via Redis Pub/Sub for Django consumption
"""

import json
import time
from datetime import datetime, timezone
from typing import Any

import redis

from app.domain.process import RateLimitExceededResponse


class RedisAdapter:
    """Redis adapter for rate limiting and event publishing.

    Uses Redis for:
    - Sliding window rate limiting per tenant
    - Pub/Sub event publishing for rate limit notifications
    """

    RATE_LIMIT_CHANNEL = "rate_limit_events"
    PLAN_CACHE_TTL = 300  # 5 minutes — short enough for near-real-time plan changes

    def __init__(self, redis_url: str):
        self._redis = redis.from_url(
            redis_url,
            decode_responses=True,
        )

    def check_rate_limit(
        self,
        tenant_id: str,
        user_id: str,
        limit: int,
        window_seconds: int = 60,
    ) -> tuple[bool, int, int]:
        """Check per-minute rate limit using sliding window (per user).

        Args:
            tenant_id: Kept for backwards compat — not used in key
            user_id: The user ID (rate limit is per user, not per tenant)
            limit: Max requests per window
            window_seconds: Window size in seconds (default 60)

        Returns:
            Tuple of (allowed, remaining, retry_after_seconds)
        """
        key = f"rl:min:{user_id}"
        now = time.time()
        window_start = now - window_seconds

        pipe = self._redis.pipeline()

        pipe.zremrangebyscore(key, 0, window_start)

        pipe.zcard(key)

        pipe.zadd(key, {str(now): now})

        pipe.expire(key, window_seconds)

        results = pipe.execute()
        current_count = results[1]

        if current_count >= limit:
            oldest = self._redis.zrange(key, 0, 0, withscores=True)
            if oldest:
                retry_after = int(oldest[0][1] + window_seconds - now) + 1
            else:
                retry_after = window_seconds
            return False, 0, max(1, retry_after)

        remaining = max(0, limit - current_count - 1)
        return True, remaining, 0

    def publish_rate_limit_event(
        self,
        tenant_id: str,
        user_id: str,
        endpoint: str,
        retry_after: int,
    ) -> None:
        """Publish rate limit exceeded event to Redis Pub/Sub.

        Django will consume this event and notify the user.

        Args:
            tenant_id: The tenant ID
            user_id: The user ID
            endpoint: The endpoint that was rate limited
            retry_after: Seconds until the user can retry
        """
        event = {
            "event_type": "rate_limit_exceeded",
            "tenant_id": tenant_id,
            "user_id": user_id,
            "endpoint": endpoint,
            "retry_after_seconds": retry_after,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self._redis.publish(self.RATE_LIMIT_CHANNEL, json.dumps(event))

    def get_quota_usage(self, user_id: str) -> dict:
        """Return current hour and day usage counters without incrementing."""
        now = datetime.now(timezone.utc)
        hour_key = f"rl:hour:{user_id}:{now.strftime('%Y%m%d%H')}"
        day_key = f"rl:day:{user_id}:{now.strftime('%Y%m%d')}"
        return {
            "hour_usage": int(self._redis.get(hour_key) or 0),
            "day_usage": int(self._redis.get(day_key) or 0),
        }

    def get_plan_cache(self, user_id: str) -> dict | None:
        """Return cached plan limits for the user, or None if not cached."""
        data = self._redis.get(f"plan:{user_id}")
        return json.loads(data) if data else None

    def set_plan_cache(self, user_id: str, plan_data: dict) -> None:
        """Cache plan limits for the user with TTL."""
        self._redis.setex(f"plan:{user_id}", self.PLAN_CACHE_TTL, json.dumps(plan_data))

    def check_quota(self, user_id: str, period: str, limit: int, window_seconds: int) -> tuple[bool, int]:
        """Check hourly or daily quota using a fixed counter with TTL.

        Returns:
            Tuple of (allowed, remaining)
        """
        now = datetime.now(timezone.utc)
        slot = now.strftime("%Y%m%d%H") if period == "hour" else now.strftime("%Y%m%d")
        key = f"rl:{period}:{user_id}:{slot}"

        current = self._redis.get(key)
        count = int(current) if current else 0

        if count >= limit:
            return False, 0

        pipe = self._redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, window_seconds)
        pipe.execute()

        return True, max(0, limit - count - 1)

    def get_rate_limit_status(
        self, tenant_id: str, user_id: str, limit: int, window_seconds: int = 60
    ) -> dict[str, Any]:
        """Get current per-minute rate limit status without incrementing."""
        key = f"rl:min:{user_id}"
        now = time.time()
        window_start = now - window_seconds

        self._redis.zremrangebyscore(key, 0, window_start)
        current_count = self._redis.zcard(key)

        return {
            "limit": limit,
            "remaining": max(0, limit - current_count),
            "window_seconds": window_seconds,
            "current_usage": current_count,
        }

    def ping(self) -> bool:
        """Check Redis connectivity.

        Returns:
            True if Redis is reachable
        """
        try:
            return self._redis.ping()
        except redis.RedisError:
            return False

    def close(self) -> None:
        """Close Redis connection."""
        self._redis.close()
