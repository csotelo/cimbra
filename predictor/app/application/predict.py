"""CRISP-DM Fase 6: Despliegue — inferencia horaria sobre observaciones nuevas.

Escala SENAMHI (alineada con tesis, sección 2.X.3):
  Nivel 1 Verde    → prob < 0.30
  Nivel 2 Amarillo → 0.30 ≤ prob < 0.60
  Nivel 3 Naranja  → 0.60 ≤ prob < 0.85
  Nivel 4 Rojo     → prob ≥ 0.85
"""
import logging
import os
from datetime import datetime, timezone

import joblib
import numpy as np
import tensorflow as tf

from app.infrastructure.postgres import PostgresAdapter

logger = logging.getLogger("predictor.predict")

FEATURES = ["temperature", "humidity", "pressure", "cape", "k_index"]

LEVEL_THRESHOLDS = [(0.85, 4), (0.60, 3), (0.30, 2)]


def _level(prob: float) -> int:
    for threshold, level in LEVEL_THRESHOLDS:
        if prob >= threshold:
            return level
    return 1


class PredictUseCase:
    def __init__(self, db: PostgresAdapter):
        self._db = db
        self._model = None
        self._scaler = None
        self._model_version = ""

    def _load_model(self, model_path: str, scaler_path: str, version: str):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Modelo no encontrado: {model_path}. Ejecuta el trainer primero.")
        if not os.path.exists(scaler_path):
            raise FileNotFoundError(f"Scaler no encontrado: {scaler_path}.")
        logger.info(f"Cargando modelo {version}...")
        self._model = tf.keras.models.load_model(model_path)
        self._scaler = joblib.load(scaler_path)
        self._model_version = version
        logger.info("Modelo cargado.")

    def execute(self):
        artifact = self._db.get_active_model()
        if not artifact:
            logger.warning("Sin modelo activo en BD. Ejecuta el trainer primero.")
            return

        if artifact["version"] != self._model_version:
            self._load_model(artifact["model_path"], artifact["scaler_path"], artifact["version"])

        stations = self._db.get_active_stations()
        if not stations:
            logger.warning("Sin estaciones activas.")
            return

        generated_at = datetime.now(tz=timezone.utc)
        total = 0

        for station in stations:
            obs = self._db.get_latest_observation(station["id"])
            if not obs:
                logger.debug(f"{station['code']}: sin observación reciente con datos completos")
                continue

            features = np.array([[obs[f] for f in FEATURES]], dtype=np.float32)
            features_scaled = self._scaler.transform(features)
            prob = float(self._model.predict(features_scaled, verbose=0)[0][0])
            level = _level(prob)

            self._db.insert_alert(
                station_id=station["id"],
                observation_id=obs["id"],
                probability=prob,
                alert_level=level,
                generated_at=generated_at,
                model_version=self._model_version,
            )
            total += 1
            logger.info(f"{station['code']} [{station['department']}] → prob={prob:.3f} nivel={level}")

        logger.info(f"Ciclo predictor: {total} alertas generadas")
