HEARTBEAT_TASKS = frozenset({
    "apps.watchdog.tasks.send_heartbeat_ping",
    "celery.backend_cleanup",
})
