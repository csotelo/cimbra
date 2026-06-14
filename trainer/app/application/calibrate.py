"""CRISP-DM Fase 5 (Calibración): Platt Scaling sobre probabilidades del modelo.

Ajusta un LogisticRegression sobre las probabilidades crudas del modelo en el
conjunto de validación. Los umbrales de alerta SENAMHI se derivan del umbral
óptimo calculado por la estadística J de Youden, no son arbitrarios.

Umbrales base SENAMHI:
  Verde < verde_amarillo ≤ Amarillo < amarillo_naranja ≤ Naranja < naranja_rojo ≤ Rojo

El umbral verde_amarillo se calcula como el punto que maximiza sensibilidad +
especificidad - 1. Los demás se derivan proporcionalmente preservando los ratios
originales (0.30 : 0.60 : 0.85 ≈ 1 : 2 : 2.83).
"""
import logging

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_curve

logger = logging.getLogger("trainer.calibrate")

# Ratios entre umbrales SENAMHI (preservados en calibración)
_RATIO_NARANJA = 2.0     # 0.60 / 0.30
_RATIO_ROJO = 2.833      # 0.85 / 0.30


def calibrate_and_compute_thresholds(model, X_val: np.ndarray, y_val: np.ndarray,
                                      calibrator_path: str) -> dict:
    """
    Aplica Platt Scaling y computa umbrales SENAMHI óptimos.
    Retorna dict con thresholds para uso en el predictor.
    """
    logger.info("Iniciando calibración Platt Scaling...")

    # Probabilidades crudas del modelo en validación
    raw_probs = model.predict(X_val, verbose=0).flatten()

    # Platt Scaling: regresión logística sobre probabilidades crudas
    calibrator = LogisticRegression(C=1.0, solver="lbfgs", max_iter=200)
    calibrator.fit(raw_probs.reshape(-1, 1), y_val)
    joblib.dump(calibrator, calibrator_path)
    logger.info(f"Calibrador guardado: {calibrator_path}")

    # Probabilidades calibradas
    cal_probs = calibrator.predict_proba(raw_probs.reshape(-1, 1))[:, 1]

    # Umbral óptimo: Youden's J = max(TPR - FPR)
    has_both = len(np.unique(y_val)) > 1
    if has_both:
        fpr, tpr, thresh_curve = roc_curve(y_val, cal_probs)
        j_idx = int(np.argmax(tpr - fpr))
        optimal = float(thresh_curve[j_idx])
    else:
        optimal = 0.30
        logger.warning("Solo una clase en validación — usando umbral por defecto 0.30")

    # Forzar rango razonable para verde/amarillo
    t_va = float(np.clip(optimal, 0.10, 0.50))
    t_an = float(np.clip(t_va * _RATIO_NARANJA, t_va + 0.05, 0.85))
    t_nr = float(np.clip(t_va * _RATIO_ROJO, t_an + 0.05, 0.98))

    thresholds = {
        "verde_amarillo": round(t_va, 3),
        "amarillo_naranja": round(t_an, 3),
        "naranja_rojo": round(t_nr, 3),
    }

    logger.info(f"Umbral Youden óptimo (crudo): {optimal:.4f}")
    logger.info(f"Umbrales SENAMHI calibrados: Verde<{t_va:.3f}  "
                f"Amarillo<{t_an:.3f}  Naranja<{t_nr:.3f}  Rojo≥{t_nr:.3f}")
    return thresholds
