"""Cliente Open-Meteo Archive API — datos históricos gratuitos sin API key.

Cubre datos desde 1940 hasta ~5 días atrás.
Usado por el trainer para construir el dataset de entrenamiento 2024-2025.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

import httpx

logger = logging.getLogger("trainer.archive")

BASE_URL = "https://archive-api.open-meteo.com/v1/archive"

HOURLY_VARS = [
    "temperature_2m",
    "relative_humidity_2m",
    "surface_pressure",
    "cape",
    "temperature_850hPa",
    "temperature_700hPa",
    "temperature_500hPa",
    "relative_humidity_850hPa",
    "relative_humidity_700hPa",
]


def _k_index(t850: Optional[float], t700: Optional[float], t500: Optional[float],
             rh850: Optional[float], rh700: Optional[float]) -> Optional[float]:
    if any(v is None for v in [t850, t700, t500, rh850, rh700]):
        return None
    td850 = t850 - (100 - rh850) / 5
    td700 = t700 - (100 - rh700) / 5
    return (t850 - t500) + td850 - (t700 - td700)


def fetch_historical(lat: float, lon: float, start: str, end: str) -> list[dict]:
    """Descarga datos horarios históricos para un rango de fechas (YYYY-MM-DD)."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start,
        "end_date": end,
        "hourly": ",".join(HOURLY_VARS),
        "timezone": "America/Lima",
    }
    try:
        resp = httpx.get(BASE_URL, params=params, timeout=120)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        logger.error(f"Archive API error ({lat},{lon}): {exc}")
        return []

    data = resp.json()
    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    if not times:
        return []

    results = []
    for i, ts in enumerate(times):
        def val(key, idx=i):
            arr = hourly.get(key, [])
            v = arr[idx] if idx < len(arr) else None
            return v

        t850 = val("temperature_850hPa")
        t700 = val("temperature_700hPa")
        t500 = val("temperature_500hPa")
        rh850 = val("relative_humidity_850hPa")
        rh700 = val("relative_humidity_700hPa")

        results.append({
            "observed_at": datetime.fromisoformat(ts).replace(tzinfo=timezone.utc),
            "temperature": val("temperature_2m"),
            "humidity": val("relative_humidity_2m"),
            "pressure": val("surface_pressure"),
            "cape": val("cape"),
            "k_index": _k_index(t850, t700, t500, rh850, rh700),
            "source": "open-meteo-archive",
            "raw": {k: val(k) for k in HOURLY_VARS},
        })

    return results
