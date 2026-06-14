"""CRISP-DM Fase 6: Despliegue — inferencia horaria con IA analítica completa.

Soporta dos arquitecturas de modelo:
  - MLP:  input (1, 5)          — usa la última observación disponible
  - LSTM: input (1, seq_len, 5) — usa las últimas seq_len observaciones

Escala SENAMHI — umbrales calibrados por Platt Scaling (Youden's J):
  Nivel 1 Verde    → prob < verde_amarillo
  Nivel 2 Amarillo → verde_amarillo ≤ prob < amarillo_naranja
  Nivel 3 Naranja  → amarillo_naranja ≤ prob < naranja_rojo
  Nivel 4 Rojo     → prob ≥ naranja_rojo

Si el calibrador no está disponible, se usan umbrales fijos SENAMHI (0.30/0.60/0.85).
Si SHAP background no está disponible, explanation_json queda None.
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
SEQ_LEN = 6

# Umbrales por defecto si no hay calibración disponible
DEFAULT_THRESHOLDS = {
    "verde_amarillo": 0.30,
    "amarillo_naranja": 0.60,
    "naranja_rojo": 0.85,
}


class PredictUseCase:
    def __init__(self, db: PostgresAdapter):
        self._db = db
        self._model = None
        self._scaler = None
        self._calibrator = None
        self._thresholds = DEFAULT_THRESHOLDS.copy()
        self._shap_background = None
        self._model_version = ""
        self._model_type = "mlp"

    def _level(self, prob: float) -> int:
        t = self._thresholds
        if prob >= t["naranja_rojo"]:     return 4
        if prob >= t["amarillo_naranja"]: return 3
        if prob >= t["verde_amarillo"]:   return 2
        return 1

    def _calibrate(self, raw_prob: float) -> float:
        if self._calibrator is None:
            return raw_prob
        return float(self._calibrator.predict_proba([[raw_prob]])[:, 1][0])

    def _load_model(self, artifact: dict):
        model_path = artifact["model_path"]
        scaler_path = artifact["scaler_path"]
        version = artifact["version"]

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Modelo no encontrado: {model_path}. Ejecuta el trainer primero.")
        if not os.path.exists(scaler_path):
            raise FileNotFoundError(f"Scaler no encontrado: {scaler_path}.")

        logger.info(f"Cargando modelo {version} ({artifact.get('model_type', 'mlp').upper()})...")
        self._model = tf.keras.models.load_model(model_path)
        self._scaler = joblib.load(scaler_path)
        self._model_type = artifact.get("model_type") or "mlp"
        self._model_version = version

        # Calibrador Platt Scaling
        cal_path = artifact.get("calibrator_path", "")
        if cal_path and os.path.exists(cal_path):
            self._calibrator = joblib.load(cal_path)
            logger.info("Calibrador Platt Scaling cargado.")
        else:
            self._calibrator = None
            logger.info("Sin calibrador — usando umbrales fijos SENAMHI.")

        # Umbrales calibrados
        t = artifact.get("thresholds_json")
        self._thresholds = t if isinstance(t, dict) and len(t) == 3 else DEFAULT_THRESHOLDS.copy()
        logger.info(f"Umbrales activos: {self._thresholds}")

        # Background SHAP para explicabilidad per-predicción
        bg_path = artifact.get("shap_background_path", "")
        if bg_path and os.path.exists(bg_path):
            self._shap_background = np.load(bg_path)
            logger.info(f"SHAP background cargado: {self._shap_background.shape}")
        else:
            self._shap_background = None

        logger.info("Modelo cargado.")

    def _shap_explanation(self, X_input: np.ndarray) -> dict | None:
        """Computa SHAP values para una predicción individual. Retorna None si falla."""
        if self._shap_background is None or self._model is None:
            return None
        try:
            import shap
            explainer = shap.DeepExplainer(self._model, self._shap_background)
            sv = explainer.shap_values(X_input)
            if isinstance(sv, list):
                sv = sv[0]
            sv = np.array(sv)
            if self._model_type == "lstm" and sv.ndim == 3:
                sv_mean = sv[0].mean(axis=0)
            else:
                sv_mean = sv[0]
            return {FEATURES[i]: round(float(sv_mean[i]), 6) for i in range(len(FEATURES))}
        except Exception as exc:
            logger.debug(f"SHAP per-prediction falló: {exc}")
            return None

    def execute(self):
        artifact = self._db.get_active_model()
        if not artifact:
            logger.warning("Sin modelo activo en BD. Ejecuta el trainer primero.")
            return

        if artifact["version"] != self._model_version:
            try:
                self._load_model(artifact)
            except (FileNotFoundError, OSError) as exc:
                logger.error(f"Modelo no disponible, saltando ciclo: {exc}")
                return

        stations = self._db.get_active_stations()
        if not stations:
            logger.warning("Sin estaciones activas.")
            return

        generated_at = datetime.now(tz=timezone.utc)
        total = 0

        for station in stations:
            obs_id = None
            features_input = None

            if self._model_type == "lstm":
                obs_list = self._db.get_last_n_observations(station["id"], n=SEQ_LEN)
                if len(obs_list) < SEQ_LEN:
                    logger.debug(f"{station['code']}: insuficientes obs para LSTM "
                                 f"({len(obs_list)}/{SEQ_LEN})")
                    continue
                obs_id = obs_list[-1]["id"]
                raw = np.array([[o[f] for f in FEATURES] for o in obs_list], dtype=np.float32)
                scaled = self._scaler.transform(raw)
                features_input = scaled[np.newaxis, :, :]  # (1, seq_len, 5)
            else:
                obs = self._db.get_latest_observation(station["id"])
                if not obs:
                    logger.debug(f"{station['code']}: sin observación reciente")
                    continue
                obs_id = obs["id"]
                raw = np.array([[obs[f] for f in FEATURES]], dtype=np.float32)
                features_input = self._scaler.transform(raw)  # (1, 5)

            raw_prob = float(self._model.predict(features_input, verbose=0)[0][0])
            prob = self._calibrate(raw_prob)
            level = self._level(prob)
            explanation = self._shap_explanation(features_input)

            self._db.insert_alert(
                station_id=station["id"],
                observation_id=obs_id,
                probability=prob,
                alert_level=level,
                generated_at=generated_at,
                model_version=self._model_version,
                explanation_json=explanation,
            )
            total += 1
            logger.info(
                f"{station['code']} [{station['department']}] "
                f"prob_raw={raw_prob:.3f} → prob_cal={prob:.3f} nivel={level} "
                f"shap={'ok' if explanation else 'n/a'}"
            )

        logger.info(f"Ciclo predictor: {total} alertas generadas")
