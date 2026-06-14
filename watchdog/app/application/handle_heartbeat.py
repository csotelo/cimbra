"""Use case: process a heartbeat ping and acknowledge it."""

import time
import logging

from app.domain.heartbeat import HeartbeatPing
from app.infrastructure.redis_adapter import RedisAdapter

logger = logging.getLogger(__name__)


class HandleHeartbeatUseCase:
    def __init__(self, redis_adapter: RedisAdapter):
        self._redis = redis_adapter

    def execute(self, raw: dict) -> None:
        ping = HeartbeatPing(
            ping_id=raw.get("ping_id", "unknown"),
            sent_at=float(raw.get("sent_at", time.time())),
            source=raw.get("source", "unknown"),
        )
        latency_ms = int((time.time() - ping.sent_at) * 1000)
        self._redis.write_last_seen(ping.ping_id, latency_ms)
