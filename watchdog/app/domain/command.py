"""WatchdogCommand domain entity."""

from dataclasses import dataclass


@dataclass
class WatchdogCommand:
    command_id: str
    action: str
    payload: dict
    user_id: str
