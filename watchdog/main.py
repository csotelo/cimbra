"""Watchdog — inter-service monitor and command executor.

Runs two consumers in parallel threads:
  1. Heartbeat consumer  → stream:heartbeat   (pattern 1: health)
  2. Command consumer    → commands:watchdog  (pattern 3: remote commands)
"""

import logging
import os
import signal
import threading
import time

from dotenv import load_dotenv

from app.application.handle_command import HandleCommandUseCase
from app.application.handle_heartbeat import HandleHeartbeatUseCase
from app.infrastructure.redis_adapter import RedisAdapter

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("watchdog")

HEARTBEAT_STREAM = "stream:heartbeat"
COMMAND_STREAM = "commands:watchdog"
GROUP = "watchdog-group"
CONSUMER = "watchdog-1"

running = True


def consumer_loop(stream: str, use_case, adapter: RedisAdapter, label: str):
    """Generic consumer loop for a Redis Stream."""
    adapter.ensure_consumer_group(stream, GROUP)
    logger.info(f"[{label}] Listening on {stream}")

    while running:
        try:
            messages = adapter.read_messages(stream, GROUP, CONSUMER, count=10, block_ms=5000)
            for msg_id, data in messages:
                use_case.execute(data)
                adapter.ack(stream, GROUP, msg_id)
        except Exception as e:
            logger.error(f"[{label}] Error: {e}")
            time.sleep(2)

    adapter.close()
    logger.info(f"[{label}] Stopped.")


def main():
    global running

    redis_url = os.getenv("REDIS_URL", "redis://redis:6379")

    heartbeat_adapter = RedisAdapter(redis_url)
    command_adapter = RedisAdapter(redis_url)

    heartbeat_uc = HandleHeartbeatUseCase(heartbeat_adapter)
    command_uc = HandleCommandUseCase(command_adapter)

    def stop(sig, frame):
        global running
        logger.info("Shutting down...")
        running = False

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    t_heartbeat = threading.Thread(
        target=consumer_loop,
        args=(HEARTBEAT_STREAM, heartbeat_uc, heartbeat_adapter, "heartbeat"),
        daemon=True,
    )
    t_command = threading.Thread(
        target=consumer_loop,
        args=(COMMAND_STREAM, command_uc, command_adapter, "command"),
        daemon=True,
    )

    t_heartbeat.start()
    t_command.start()

    logger.info("Watchdog running — heartbeat + command consumers active")

    while running:
        time.sleep(1)

    t_heartbeat.join(timeout=10)
    t_command.join(timeout=10)
    logger.info("Watchdog stopped.")


if __name__ == "__main__":
    main()
