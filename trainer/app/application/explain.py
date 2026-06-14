"""CRISP-DM Fase 5 (XAI): Explicabilidad con SHAP.

Computa importancia global de features (mean |SHAP|) sobre el test set y
guarda una muestra de background para inferencia en el predictor.

- MLP:  shap.DeepExplainer sobre modelo Keras, input (n, features)
- LSTM: shap.DeepExplainer sobre modelo Keras, input (n, seq_len, features)
        — los shap_values se promedian sobre la dimensión temporal.
"""
import logging

import joblib
import numpy as np

logger = logging.getLogger("trainer.explain")

FEATURE_NAMES = ["temperature", "humidity", "pressure", "cape", "k_index"]


def compute_global_importance(model, X_train: np.ndarray, X_test: np.ndarray,
                               model_type: str = "mlp") -> dict:
    """
    Retorna dict {feature: normalized_mean_abs_shap}.
    Usa las primeras 100 muestras de X_test para velocidad.
    """
    try:
        import shap

        n_bg = min(100, len(X_train))
        n_eval = min(100, len(X_test))
        background = X_train[:n_bg]
        X_eval = X_test[:n_eval]

        logger.info(f"Computando SHAP ({model_type}) — background={n_bg}, eval={n_eval}...")
        explainer = shap.DeepExplainer(model, background)
        sv = explainer.shap_values(X_eval)

        # sv puede ser lista [array] o array directo según versión de shap
        if isinstance(sv, list):
            sv = sv[0]
        sv = np.array(sv)

        if model_type == "lstm" and sv.ndim == 3:
            # (samples, seq_len, features) → media sobre muestras y timesteps
            mean_shap = np.mean(np.abs(sv), axis=(0, 1))
        else:
            # (samples, features)
            mean_shap = np.mean(np.abs(sv), axis=0)

        # Normalizar a suma 1 para interpretabilidad relativa
        total = float(mean_shap.sum())
        if total > 0:
            mean_shap = mean_shap / total

        importance = {FEATURE_NAMES[i]: round(float(mean_shap[i]), 4)
                      for i in range(len(FEATURE_NAMES))}

        ranked = sorted(importance.items(), key=lambda x: x[1], reverse=True)
        logger.info("Feature importance global (SHAP normalizado):")
        for feat, val in ranked:
            logger.info(f"  {feat}: {val:.4f}")

        return importance

    except Exception as exc:
        logger.warning(f"SHAP global falló: {exc}. Devolviendo importancia uniforme.")
        uniform = round(1.0 / len(FEATURE_NAMES), 4)
        return {f: uniform for f in FEATURE_NAMES}


def save_shap_background(X_train: np.ndarray, background_path: str, n_samples: int = 100):
    """Guarda muestra de background como .npy para uso del predictor."""
    bg = X_train[:min(n_samples, len(X_train))]
    np.save(background_path, bg)
    logger.info(f"Background SHAP guardado: {background_path} ({len(bg)} muestras)")


def shap_for_prediction(model, background: np.ndarray, X_input: np.ndarray,
                         model_type: str = "mlp") -> dict:
    """
    Computa SHAP values para UNA predicción individual.
    Retorna {feature: shap_value} (valores sin normalizar, para interpretación directa).
    """
    try:
        import shap
        explainer = shap.DeepExplainer(model, background)
        sv = explainer.shap_values(X_input)
        if isinstance(sv, list):
            sv = sv[0]
        sv = np.array(sv)

        if model_type == "lstm" and sv.ndim == 3:
            # (1, seq_len, features) → media sobre timesteps
            sv_mean = sv[0].mean(axis=0)
        else:
            sv_mean = sv[0]

        return {FEATURE_NAMES[i]: round(float(sv_mean[i]), 6) for i in range(len(FEATURE_NAMES))}

    except Exception as exc:
        logger.debug(f"SHAP per-prediction falló: {exc}")
        return {}
