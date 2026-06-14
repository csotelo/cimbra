"""Redis adapter — Stream consumer + last_seen writer."""

import json
import logging
from datetime import datetime, timezone

import redis

logger = logging.getLogger(__name__)

SERVICE_NAME = "watchdog"
LAST_SEEN_TTL = 120  # seconds — if not refreshed, considered DOWN


class RedisAdapter:
    def __init__(self, redis_url: str):
        self._r = redis.from_url(redis_url, decode_responses=True)

    def ensure_consumer_group(self, stream: str, group: str):
        """Create stream + consumer group if they don't exist."""
        try:
            self._r.xgroup_create(stream, group, id="0", mkstream=True)
        except redis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise

    def read_messages(
        self, stream: str, group: str, consumer: str, count: int = 10, block_ms: int = 5000
    ) -> list[tuple[str, dict]]:
        result = self._r.xreadgroup(
            group, consumer, {stream: ">"}, count=count, block=block_ms
        )
        if not result:
            return []
        return [(msg_id, data) for msg_id, data in result[0][1]]

    def ack(self, stream: str, group: str, msg_id: str):
        self._r.xack(stream, group, msg_id)

    def write_last_seen(self, ping_id: str, latency_ms: int):
        """Write service health status to Redis with TTL."""
        key = f"service:{SERVICE_NAME}:last_seen"
        payload = {
            "service": SERVICE_NAME,
            "status": "ok",
            "last_seen": datetime.now(timezone.utc).isoformat(),
            "ping_id": ping_id,
            "latency_ms": latency_ms,
        }
        self._r.setex(key, LAST_SEEN_TTL, json.dumps(payload))
        logger.info(f"[{SERVICE_NAME}] ping_id={ping_id} latency={latency_ms}ms — last_seen updated")

    def write_command_result(self, command_id: str, status: str, output: dict, ttl: int = 300):
        """Write command execution result to Redis with TTL (default 5 min)."""
        import json
        from datetime import datetime, timezone
        key = f"result:watchdog:{command_id}"
        payload = {
            "command_id": command_id,
            "status": status,
            "output": output,
            "executed_at": datetime.now(timezone.utc).isoformat(),
        }
        self._r.setex(key, ttl, json.dumps(payload))

    def close(self):
        self._r.close()
