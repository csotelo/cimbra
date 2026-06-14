import logging

from app.infrastructure.open_meteo import fetch_observations
from app.infrastructure.postgres import PostgresAdapter

logger = logging.getLogger("ingestor.application")


class IngestWeatherUseCase:
    def __init__(self, db: PostgresAdapter):
        self._db = db

    def execute(self):
        stations = self._db.get_active_stations()
        if not stations:
            logger.warning("No hay estaciones activas en BD — ejecuta seed_stations en Django")
            return

        total_inserted = 0
        for station in stations:
            observations = fetch_observations(
                lat=float(station["latitude"]),
                lon=float(station["longitude"]),
            )
            if not observations:
                logger.warning(f"Sin datos para {station['code']}")
                continue

            inserted = self._db.upsert_observations(station["id"], observations)
            total_inserted += inserted
            logger.info(f"{station['code']} — {inserted}/{len(observations)} registros nuevos")

        logger.info(f"Ciclo completo: {total_inserted} observaciones insertadas en total")
