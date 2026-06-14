"""Adaptador PostgreSQL para el trainer — lee observaciones, escribe model_artifacts."""
import json
import logging
import uuid
from datetime import datetime

import psycopg2
import psycopg2.extras

logger = logging.getLogger("trainer.postgres")


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

    def get_active_stations(self) -> list[dict]:
        with self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT id, code, latitude, longitude FROM weather_stations WHERE is_active = TRUE"
            )
            return [dict(r) for r in cur.fetchall()]

    def count_observations(self) -> int:
        with self._conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM weather_observations WHERE cape IS NOT NULL AND k_index IS NOT NULL")
            return cur.fetchone()[0]

    def upsert_observations(self, station_id: int, observations: list[dict]) -> int:
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
                        obs.get("source", "open-meteo-archive"),
                        json.dumps(obs.get("raw", {})),
                    ),
                )
                if cur.rowcount:
                    inserted += 1
        self._conn.commit()
        return inserted

    def load_dataset(self) -> list[dict]:
        """Carga todas las observaciones ordenadas cronológicamente."""
        with self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, temperature, humidity, pressure, cape, k_index, observed_at
                FROM weather_observations
                WHERE cape IS NOT NULL
                  AND k_index IS NOT NULL
                  AND temperature IS NOT NULL
                  AND humidity IS NOT NULL
                  AND pressure IS NOT NULL
                ORDER BY observed_at
                """
            )
            return [dict(r) for r in cur.fetchall()]

    def create_artifact(self, version: str, model_path: str, scaler_path: str) -> str:
        artifact_id = str(uuid.uuid4())
        with self._conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO model_artifacts (id, version, model_path, scaler_path, status, created_at)
                VALUES (%s, %s, %s, %s, 'training', NOW())
                """,
                (artifact_id, version, model_path, scaler_path),
            )
        self._conn.commit()
        return artifact_id

    def update_artifact(self, artifact_id: str, **kwargs):
        """Actualiza campos del artefacto. Serializa dicts/listas a JSON automáticamente."""
        if not kwargs:
            return
        processed = {
            k: (json.dumps(v) if isinstance(v, (dict, list)) else v)
            for k, v in kwargs.items()
        }
        sets = ", ".join(f"{k} = %s" for k in processed)
        values = list(processed.values()) + [artifact_id]
        with self._conn.cursor() as cur:
            cur.execute(f"UPDATE model_artifacts SET {sets} WHERE id = %s", values)
        self._conn.commit()

    def activate_artifact(self, artifact_id: str):
        """Marca este artefacto como activo y desactiva los anteriores."""
        with self._conn.cursor() as cur:
            cur.execute("UPDATE model_artifacts SET is_active = FALSE WHERE is_active = TRUE")
            cur.execute("UPDATE model_artifacts SET is_active = TRUE WHERE id = %s", (artifact_id,))
        self._conn.commit()

    def save_benchmark(self, artifact_id: str, model_type: str, cv_fold: int, metrics: dict):
        """Guarda resultado de un fold del benchmark en model_benchmarks."""
        with self._conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO model_benchmarks
                    (artifact_id, model_type, cv_fold, accuracy, precision, recall,
                     f1, roc_auc, training_seconds, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                """,
                (
                    artifact_id,
                    model_type,
                    cv_fold,
                    metrics.get("accuracy", 0),
                    metrics.get("precision", 0),
                    metrics.get("recall", 0),
                    metrics.get("f1", 0),
                    metrics.get("roc_auc", 0),
                    metrics.get("training_seconds", 0),
                ),
            )
        self._conn.commit()
