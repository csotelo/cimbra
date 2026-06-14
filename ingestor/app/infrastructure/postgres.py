"""Adaptador PostgreSQL para el ingestor — escribe en las tablas definidas por Django."""
import json
import logging
from datetime import datetime

import psycopg2
import psycopg2.extras

logger = logging.getLogger("ingestor.postgres")


class PostgresAdapter:
    def __init__(self, db_url: str):
        self._url = db_url
        self._conn = None

    def connect(self):
        self._conn = psycopg2.connect(self._url)
        self._conn.autocommit = False
        logger.info("PostgreSQL conectado")

    def close(self):
        if self._conn:
            self._conn.close()

    def ping(self) -> bool:
        try:
            with self._conn.cursor() as cur:
                cur.execute("SELECT 1")
            return True
        except Exception:
            return False

    def reconnect(self):
        try:
            self.close()
        except Exception:
            pass
        self.connect()

    def get_active_stations(self) -> list[dict]:
        with self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT id, code, name, department, "
                "ST_Y(location::geometry) AS latitude, "
                "ST_X(location::geometry) AS longitude, "
                "altitude_m "
                "FROM weather_stations WHERE is_active = TRUE ORDER BY code"
            )
            return [dict(r) for r in cur.fetchall()]

    def upsert_observations(self, station_id: int, observations: list[dict]) -> int:
        """Inserta observaciones ignorando duplicados (ON CONFLICT DO NOTHING)."""
        if not observations:
            return 0
        inserted = 0
        with self._conn.cursor() as cur:
            for obs in observations:
                cur.execute(
                    """
                    INSERT INTO weather_observations
                        (station_id, observed_at, temperature, humidity, pressure, cape, k_index, source, raw_data, ingested_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (station_id, observed_at) DO NOTHING
                    """,
                    (
                        station_id,
                        obs["observed_at"],
                        obs.get("temperature"),
                        obs.get("humidity"),
                        obs.get("pressure"),
                        obs.get("cape"),
                        obs.get("k_index"),
                        obs.get("source", "open-meteo"),
                        json.dumps(obs.get("raw", {})),
                    ),
                )
                if cur.rowcount:
                    inserted += 1
        self._conn.commit()
        return inserted
