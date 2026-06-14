"""CRISP-DM Fase 2-3: Comprensión y preparación de datos.

Descarga datos históricos 2024-2025 desde Open-Meteo Archive para cada estación
activa. Solo inserta si la BD tiene menos de MIN_SAMPLES registros útiles.
"""
import logging

from app.infrastructure.open_meteo_archive import fetch_historical
from app.infrastructure.postgres import PostgresAdapter

logger = logging.getLogger("trainer.fetch_history")

HISTORY_START = "2024-01-01"
HISTORY_END = "2025-12-31"
MIN_SAMPLES = 5000


def backfill_if_needed(db: PostgresAdapter) -> int:
    count = db.count_observations()
    logger.info(f"Observaciones útiles en BD: {count}")

    if count >= MIN_SAMPLES:
        logger.info("Dataset suficiente — no se requiere backfill histórico")
        return count

    logger.info(f"Insuficiente ({count} < {MIN_SAMPLES}) — iniciando backfill histórico {HISTORY_START}/{HISTORY_END}")
    stations = db.get_active_stations()

    total_inserted = 0
    for station in stations:
        logger.info(f"Descargando histórico para {station['code']}...")
        observations = fetch_historical(
            lat=float(station["latitude"]),
            lon=float(station["longitude"]),
            start=HISTORY_START,
            end=HISTORY_END,
        )
        if not observations:
            logger.warning(f"Sin datos históricos para {station['code']}")
            continue

        inserted = db.upsert_observations(station["id"], observations)
        total_inserted += inserted
        logger.info(f"{station['code']}: {inserted}/{len(observations)} registros históricos insertados")

    final_count = db.count_observations()
    logger.info(f"Backfill completo: {total_inserted} nuevos — total útil: {final_count}")
    return final_count
