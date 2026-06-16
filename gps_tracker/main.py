"""GPS Tracker — subscribes to MQTT positions, writes Redis + batches to PostgreSQL."""

import asyncio
import json
import logging
import os
from collections import deque
from datetime import datetime, timezone

import aiomqtt
import asyncpg
import redis.asyncio as aioredis
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

MQTT_HOST = os.getenv("MQTT_HOST", "mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
DB_URL = os.getenv("DB_URL", "postgresql://postgres:postgres@postgres:5432/multitenant_db")
BATCH_INTERVAL = int(os.getenv("BATCH_INTERVAL_SEC", "10"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "500"))

# Topic: ximbra/{tenant_id}/tracking/{entity_type}/{entity_id}/position
TOPIC = "ximbra/+/tracking/+/+/position"

buffer: deque = deque()


def _pg_url(url: str) -> str:
    """asyncpg requires postgres:// scheme."""
    return url.replace("postgresql://", "postgres://", 1) if url.startswith("postgresql://") else url


async def process_message(msg, redis_conn: aioredis.Redis) -> None:
    parts = msg.topic.value.split("/")
    if len(parts) != 6 or parts[0] != "ximbra" or parts[2] != "tracking" or parts[5] != "position":
        return

    _, tenant_id, _, entity_type, entity_id, _ = parts

    try:
        payload = json.loads(msg.payload)
        lat = float(payload["lat"])
        lon = float(payload["lon"])
        accuracy = float(payload.get("accuracy", 0.0))
        ts = payload.get("ts", datetime.now(timezone.utc).isoformat())
    except Exception as exc:
        log.warning("Malformed payload on %s: %s — %s", msg.topic.value, msg.payload, exc)
        return

    # Update Redis hash — last known position per entity
    value = json.dumps({
        "entity_type": entity_type,
        "entity_id": entity_id,
        "lat": lat,
        "lon": lon,
        "accuracy": accuracy,
        "ts": ts,
    })
    redis_key = f"tracking:last_position:{tenant_id}"
    await redis_conn.hset(redis_key, f"{entity_type}:{entity_id}", value)
    await redis_conn.expire(redis_key, 86400)  # 24 h TTL

    buffer.append((tenant_id, entity_id, entity_type, lat, lon, accuracy, ts))
    log.debug("Buffered %s/%s lat=%s lon=%s (buffer=%d)", entity_type, entity_id, lat, lon, len(buffer))


async def flush_buffer(db_pool: asyncpg.Pool) -> None:
    if not buffer:
        return
    rows = []
    while buffer and len(rows) < BATCH_SIZE:
        rows.append(buffer.popleft())

    async with db_pool.acquire() as conn:
        await conn.executemany(
            """
            INSERT INTO field_positions
                (tenant_id, entity_id, entity_type, latitude, longitude, accuracy, recorded_at, received_at)
            VALUES ($1::uuid, $2::uuid, $3, $4, $5, $6, $7::timestamptz, NOW())
            """,
            rows,
        )
    log.info("Flushed %d position records to PostgreSQL", len(rows))


async def batch_writer(db_pool: asyncpg.Pool) -> None:
    while True:
        await asyncio.sleep(BATCH_INTERVAL)
        try:
            await flush_buffer(db_pool)
        except Exception as exc:
            log.error("Batch write error: %s", exc)


async def main() -> None:
    log.info("GPS Tracker starting — broker=%s:%s topic=%s", MQTT_HOST, MQTT_PORT, TOPIC)
    redis_conn = await aioredis.from_url(REDIS_URL, decode_responses=True)
    db_pool = await asyncpg.create_pool(_pg_url(DB_URL), min_size=1, max_size=3)

    asyncio.create_task(batch_writer(db_pool))

    while True:
        try:
            async with aiomqtt.Client(MQTT_HOST, MQTT_PORT) as client:
                log.info("Connected to MQTT broker")
                await client.subscribe(TOPIC)
                async for msg in client.messages:
                    try:
                        await process_message(msg, redis_conn)
                        if len(buffer) >= BATCH_SIZE:
                            await flush_buffer(db_pool)
                    except Exception as exc:
                        log.error("Message error: %s", exc)
        except Exception as exc:
            log.error("MQTT disconnected: %s — reconnecting in 5s", exc)
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
