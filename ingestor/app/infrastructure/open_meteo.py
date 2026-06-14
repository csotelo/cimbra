"""Open-Meteo client — provee variables meteorológicas horarias para Perú.

Variables requeridas por el modelo NN de la tesis:
- temperature_2m      → temperatura superficial (°C)
- relative_humidity_2m → humedad relativa (%)
- surface_pressure    → presión atmosférica (hPa)
- cape                → energía convectiva disponible (J/kg)
- K-Index             → calculado de T y HR a 850/700/500 hPa
"""
import logging
import time
from datetime import datetime, timezone
from typing import Optional

import httpx

logger = logging.getLogger("ingestor.open_meteo")

BASE_URL = "https://api.open-meteo.com/v1/forecast"

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
    """K-Index = (T850 - T500) + Td850 - (T700 - Td700).
    Td ≈ T - (100 - RH) / 5  (aproximación Magnus válida para RH > 50%).
    """
    if any(v is None for v in [t850, t700, t500, rh850, rh700]):
        return None
    td850 = t850 - (100 - rh850) / 5
    td700 = t700 - (100 - rh700) / 5
    return (t850 - t500) + td850 - (t700 - td700)


def fetch_observations(lat: float, lon: float, max_retries: int = 3) -> list[dict]:
    """Descarga observaciones horarias de las últimas 24h + próximas 24h.
    Reintenta hasta max_retries veces con backoff exponencial ante 429/5xx.
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ",".join(HOURLY_VARS),
        "timezone": "America/Lima",
        "past_days": 1,
        "forecast_days": 1,
    }
    delay = 5
    resp = None
    for attempt in range(max_retries):
        try:
            resp = httpx.get(BASE_URL, params=params, timeout=30)
            resp.raise_for_status()
            break
        except httpx.HTTPStatusError as exc:
            code = exc.response.status_code
            if code in (429, 500, 502, 503) and attempt < max_retries - 1:
                logger.warning(
                    f"Open-Meteo HTTP {code} ({lat},{lon}), intento {attempt + 1}/{max_retries}, "
                    f"reintento en {delay}s"
                )
                time.sleep(delay)
                delay *= 2
            else:
                logger.error(f"Open-Meteo HTTP {code} ({lat},{lon}): {exc}")
                return []
        except httpx.HTTPError as exc:
            logger.error(f"Open-Meteo error de red ({lat},{lon}): {exc}")
            return []
    else:
        logger.error(f"Open-Meteo: {max_retries} intentos fallidos para ({lat},{lon})")
        return []

    data = resp.json()
    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    if not times:
        return []

    results = []
    for i, ts in enumerate(times):
        def val(key):
            arr = hourly.get(key, [])
            v = arr[i] if i < len(arr) else None
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
            "raw": {k: val(k) for k in HOURLY_VARS},
        })

    return results
