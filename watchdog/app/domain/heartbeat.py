"""Heartbeat domain entity."""

from dataclasses import dataclass


@dataclass
class HeartbeatPing:
    ping_id: str
    sent_at: float
    source: str
