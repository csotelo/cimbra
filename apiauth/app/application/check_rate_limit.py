"""Rate limit check use case — enforces per-minute, per-hour and per-day limits."""

from dataclasses import dataclass

from app.infrastructure.redis_adapter import RedisAdapter


@dataclass
class RateLimitResult:
    allowed: bool
    remaining: int
    retry_after_seconds: int
    limit: int
    period: str = "minute"


class CheckRateLimitUseCase:
    """Checks three complementary limits per user (not per tenant):
    1. Per-minute  — sliding window in Redis (enforcement)
    2. Per-hour    — fixed counter with TTL (quota)
    3. Per-day     — fixed counter with TTL (quota)
    """

    def __init__(self, redis_adapter: RedisAdapter, window_seconds: int = 60):
        self._redis = redis_adapter
        self._window_seconds = window_seconds

    def execute(
        self,
        user_id: str,
        rate_limit_per_minute: int,
        requests_per_hour: int,
        requests_per_day: int,
        endpoint: str,
        tenant_id: str = "",
    ) -> RateLimitResult:
        # 1. Per-minute sliding window
        allowed, remaining_min, retry_after = self._redis.check_rate_limit(
            tenant_id=tenant_id,
            user_id=user_id,
            limit=rate_limit_per_minute,
            window_seconds=self._window_seconds,
        )
        if not allowed:
            self._redis.publish_rate_limit_event(
                tenant_id=tenant_id, user_id=user_id,
                endpoint=endpoint, retry_after=retry_after,
            )
            return RateLimitResult(
                allowed=False, remaining=0,
                retry_after_seconds=retry_after, limit=rate_limit_per_minute,
                period="minute",
            )

        # 2. Per-hour quota
        allowed_h, remaining_h = self._redis.check_quota(user_id, "hour", requests_per_hour, 3600)
        if not allowed_h:
            self._redis.publish_rate_limit_event(
                tenant_id=tenant_id, user_id=user_id,
                endpoint=endpoint, retry_after=3600,
            )
            return RateLimitResult(
                allowed=False, remaining=0,
                retry_after_seconds=3600, limit=requests_per_hour,
                period="hour",
            )

        # 3. Per-day quota
        allowed_d, remaining_d = self._redis.check_quota(user_id, "day", requests_per_day, 86400)
        if not allowed_d:
            self._redis.publish_rate_limit_event(
                tenant_id=tenant_id, user_id=user_id,
                endpoint=endpoint, retry_after=86400,
            )
            return RateLimitResult(
                allowed=False, remaining=0,
                retry_after_seconds=86400, limit=requests_per_day,
                period="day",
            )

        remaining = min(remaining_min, remaining_h, remaining_d)
        return RateLimitResult(
            allowed=True, remaining=remaining,
            retry_after_seconds=0, limit=rate_limit_per_minute,
        )

    def get_status(self, tenant_id: str, user_id: str, rate_limit: int) -> dict:
        """Get per-minute status without incrementing."""
        return self._redis.get_rate_limit_status(
            tenant_id=tenant_id, user_id=user_id,
            limit=rate_limit, window_seconds=self._window_seconds,
        )
