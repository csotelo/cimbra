"""Adaptador PostgreSQL para el predictor — lee obs/modelo, escribe storm_alerts."""
import json
import logging
from datetime import datetime, timezone

import psycopg2
import psycopg2.extras

logger = logging.getLogger("predictor.postgres")


class PostgresAdapter:
    def __init__(self, db_url: str):
        self._url = db_url
        self._conn = None

    def connect(self):
        self._conn = psycopg2.connect(self._url)
        self._conn.autocommit = False

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

    def get_active_model(self) -> dict | None:
        with self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, version, model_path, scaler_path, model_type,
                       calibrator_path, thresholds_json, shap_background_path
                FROM model_artifacts
                WHERE is_active = TRUE AND status = 'ready'
                LIMIT 1
                """
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def get_active_stations(self) -> list[dict]:
        with self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT id, code, name, department FROM weather_stations WHERE is_active = TRUE"
            )
            return [dict(r) for r in cur.fetchall()]

    def get_latest_observation(self, station_id: int) -> dict | None:
        with self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, temperature, humidity, pressure, cape, k_index, observed_at
                FROM weather_observations
                WHERE station_id = %s
                  AND cape IS NOT NULL AND k_index IS NOT NULL
                  AND temperature IS NOT NULL AND humidity IS NOT NULL AND pressure IS NOT NULL
                ORDER BY observed_at DESC
                LIMIT 1
                """,
                (station_id,),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def get_last_n_observations(self, station_id: int, n: int = 6) -> list[dict]:
        """Retorna las últimas n observaciones completas, en orden cronológico."""
        with self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, temperature, humidity, pressure, cape, k_index, observed_at
                FROM weather_observations
                WHERE station_id = %s
                  AND cape IS NOT NULL AND k_index IS NOT NULL
                  AND temperature IS NOT NULL AND humidity IS NOT NULL AND pressure IS NOT NULL
                ORDER BY observed_at DESC
                LIMIT %s
                """,
                (station_id, n),
            )
            rows = cur.fetchall()
            return [dict(r) for r in reversed(rows)]  # orden cronológico

    def insert_alert(
        self,
        station_id: int,
        observation_id: int | None,
        probability: float,
        alert_level: int,
        generated_at: datetime,
        model_version: str,
        explanation_json: dict | None = None,
    ):
        with self._conn.cursor() as cur:
            cur.execute(
                "UPDATE storm_alerts SET is_active = FALSE WHERE station_id = %s AND is_active = TRUE",
                (station_id,),
            )
            cur.execute(
                """
                INSERT INTO storm_alerts
                    (station_id, observation_id, probability, alert_level, is_active,
                     generated_at, model_version, explanation_json, created_at)
                VALUES (%s, %s, %s, %s, TRUE, %s, %s, %s, NOW())
                """,
                (
                    station_id, observation_id, probability, alert_level,
                    generated_at, model_version,
                    json.dumps(explanation_json) if explanation_json else None,
                ),
            )
        self._conn.commit()
