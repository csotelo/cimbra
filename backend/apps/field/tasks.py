"""Celery tasks for field alert distance checks — FCM push to field devices."""

import json
import logging
import math
import os
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

log = logging.getLogger("field.tasks")

# Alert zones (km)
ALERT_RED_KM = 16
ALERT_YELLOW_KM = 32
FCM_COOLDOWN_MINUTES = 5  # avoid re-sending same-level alert within this window

LEVEL_LABELS = {4: "Rojo", 3: "Naranja", 2: "Amarillo", 1: "Verde"}
BUZZER_PATTERN = {4: "continuous", 3: "fast", 2: "intermittent", 1: "off"}


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


@shared_task(name="field.check_field_alerts")
def check_field_alerts():
    """
    For every tenant that has active employees with GPS positions in Redis:
    - Calculate distance from each employee to every active storm alert station.
    - If < 16 km → Alerta Roja (FCM continuous buzzer).
    - If 16–32 km → Alerta Amarilla (FCM intermittent buzzer).
    - Send FCM push to employee device token (5-min cooldown per employee).
    - Store current alert level in Redis for TrackingMap enrichment.
    """
    import redis as redis_lib
    from apps.weather.models import StormAlert
    from apps.tenants.models import Tenant
    from .models import Employee
    from .fcm import send_fcm_push

    redis_url = os.environ.get("REDIS_URL", "redis://redis:6379")
    r = redis_lib.Redis.from_url(redis_url, decode_responses=True)

    # Load all active alerts with station coordinates
    active_alerts = list(
        StormAlert.objects.filter(is_active=True, alert_level__gte=2).select_related("station")
    )
    if not active_alerts:
        log.debug("No active alerts — skipping field check")
        return

    alert_stations = [
        {
            "station_name": a.station.name,
            "station_code": a.station.code,
            "lat": a.station.location.y,
            "lon": a.station.location.x,
            "alert_level": a.alert_level,
            "probability": a.probability,
        }
        for a in active_alerts
    ]

    tenants = Tenant.objects.filter(is_active=True)
    now = timezone.now()
    fcm_sent = 0

    for tenant in tenants:
        redis_key = f"tracking:last_position:{tenant.id}"
        raw = r.hgetall(redis_key)
        if not raw:
            continue

        # Index employees by ID for fast lookup
        emp_ids = [
            field.split(":", 1)[1]
            for field in raw
            if field.startswith("employee:")
        ]
        if not emp_ids:
            continue

        employees = {
            str(e.id): e
            for e in Employee.objects.filter(id__in=emp_ids, tenant=tenant, is_active=True)
        }

        for field, value_str in raw.items():
            if not field.startswith("employee:"):
                continue
            entity_id = field.split(":", 1)[1]
            employee = employees.get(entity_id)
            if not employee or not employee.fcm_token:
                continue

            try:
                pos = json.loads(value_str)
                emp_lat = float(pos["lat"])
                emp_lon = float(pos["lon"])
            except Exception:
                continue

            # Find closest threat
            closest_level = 1  # Green — no danger
            closest_station = None
            closest_dist_km = None

            for station in alert_stations:
                dist = _haversine_km(emp_lat, emp_lon, station["lat"], station["lon"])
                candidate_level = 1
                if dist <= ALERT_RED_KM:
                    candidate_level = max(station["alert_level"], 4)
                elif dist <= ALERT_YELLOW_KM:
                    candidate_level = max(station["alert_level"], 2)

                if candidate_level > closest_level:
                    closest_level = candidate_level
                    closest_station = station
                    closest_dist_km = dist

            # Store alert level in Redis for TrackingMap (TTL = 2h)
            alert_key = f"tracking:field_alert:{entity_id}"
            r.setex(alert_key, 7200, json.dumps({
                "level": closest_level,
                "station": closest_station["station_name"] if closest_station else None,
                "distance_km": round(closest_dist_km, 1) if closest_dist_km else None,
            }))

            # Check FCM cooldown
            if closest_level <= 1:
                continue  # No push for green
            cooldown_ok = (
                employee.last_alert_sent_at is None
                or (now - employee.last_alert_sent_at) >= timedelta(minutes=FCM_COOLDOWN_MINUTES)
                or employee.last_alert_level != closest_level
            )
            if not cooldown_ok:
                continue

            # Send FCM
            level_label = LEVEL_LABELS.get(closest_level, str(closest_level))
            buzzer = BUZZER_PATTERN.get(closest_level, "intermittent")
            title = f"⚡ Alerta {level_label} — Tormenta eléctrica"
            body = (
                f"Distancia: {closest_dist_km:.1f} km — {closest_station['station_name']}. "
                f"{'¡Busca refugio de inmediato!' if closest_level >= 4 else 'Mantente alerta y evita zonas abiertas.'}"
            )
            ok = send_fcm_push(
                fcm_token=employee.fcm_token,
                title=title,
                body=body,
                data={
                    "alert_level": str(closest_level),
                    "alert_level_label": level_label,
                    "buzzer_pattern": buzzer,
                    "distance_km": str(round(closest_dist_km, 1)),
                    "station": closest_station["station_name"],
                },
            )
            if ok:
                Employee.objects.filter(id=employee.id).update(
                    last_alert_level=closest_level,
                    last_alert_sent_at=now,
                )
                fcm_sent += 1
                log.info(
                    "FCM alert sent — employee=%s level=%s dist=%.1f km station=%s",
                    employee.full_name,
                    closest_level,
                    closest_dist_km,
                    closest_station["station_name"],
                )

    log.info("check_field_alerts: %d FCM pushes sent", fcm_sent)
