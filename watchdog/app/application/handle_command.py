"""Use case: execute a remote command and write the result to Redis."""

import logging
import platform
import time

from app.domain.command import WatchdogCommand

logger = logging.getLogger(__name__)

ACTIONS = {}


def action(name):
    def decorator(fn):
        ACTIONS[name] = fn
        return fn
    return decorator


@action("echo")
def _echo(payload: dict) -> dict:
    return {"echo": payload}


@action("system_info")
def _system_info(payload: dict) -> dict:
    return {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "node": platform.node(),
        "uptime_check": "ok",
    }


@action("ping")
def _ping(payload: dict) -> dict:
    import socket
    host = payload.get("host", "redis")
    try:
        start = time.time()
        addr = socket.getaddrinfo(host, None)[0][4][0]
        latency_ms = int((time.time() - start) * 1000)
        return {"host": host, "reachable": True, "resolved": addr, "latency_ms": latency_ms}
    except socket.gaierror as e:
        return {"host": host, "reachable": False, "error": str(e)}


class HandleCommandUseCase:
    def __init__(self, redis_adapter):
        self._redis = redis_adapter

    def execute(self, raw: dict) -> None:
        cmd = WatchdogCommand(
            command_id=raw.get("command_id", "unknown"),
            action=raw.get("action", "echo"),
            payload=__import__("json").loads(raw.get("payload", "{}")),
            user_id=raw.get("user_id", ""),
        )

        handler = ACTIONS.get(cmd.action)
        if not handler:
            output = {"error": f"Unknown action: {cmd.action}"}
            status = "error"
        else:
            try:
                output = handler(cmd.payload)
                status = "ok"
            except Exception as e:
                output = {"error": str(e)}
                status = "error"

        self._redis.write_command_result(cmd.command_id, status, output)
        logger.info(f"[watchdog] command={cmd.action} id={cmd.command_id} status={status}")
