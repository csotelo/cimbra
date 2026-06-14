"""CRISP-DM Fase 4 (comparativo): Benchmark multi-modelo con walk-forward CV.

Compara MLP (sklearn proxy), Random Forest y XGBoost sobre validación temporal
expandiendo la ventana de entrenamiento (walk-forward). El objetivo es demostrar
que el modelo de tesis (red neuronal) supera o es competitivo con baselines clásicos.

Nota: se usa MLPClassifier de sklearn en el benchmark (misma arquitectura, más
eficiente para CV iterativo). El modelo Keras completo se entrena por separado.
"""
import logging
import time

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (accuracy_score, f1_score, precision_score,
                              recall_score, roc_auc_score)
from sklearn.neural_network import MLPClassifier
import xgboost as xgb

from app.application.prepare import walk_forward_splits

logger = logging.getLogger("trainer.benchmark")

MODELS = {
    "mlp": lambda: MLPClassifier(
        hidden_layer_sizes=(64, 32, 16), max_iter=100, random_state=42,
        early_stopping=True, validation_fraction=0.1,
    ),
    "rf": lambda: RandomForestClassifier(
        n_estimators=100, class_weight="balanced", random_state=42, n_jobs=-1,
    ),
    "xgb": lambda: xgb.XGBClassifier(
        n_estimators=100, scale_pos_weight=5, random_state=42,
        eval_metric="logloss", verbosity=0, use_label_encoder=False,
    ),
}


def _compute_metrics(y_true, y_pred, y_prob, elapsed: float, fold: int) -> dict:
    has_both_classes = len(np.unique(y_true)) > 1
    return {
        "cv_fold": fold,
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, y_prob)) if has_both_classes else 0.0,
        "training_seconds": round(elapsed, 2),
    }


def run_benchmark(X: np.ndarray, y: np.ndarray, n_splits: int = 4) -> dict:
    """
    Ejecuta walk-forward CV para todos los modelos.
    Retorna {model_type: {"fold_results": [...], "mean_metrics": {...}}}.
    """
    splits = walk_forward_splits(X, y, n_splits=n_splits)
    if not splits:
        logger.warning("Walk-forward: sin splits válidos (dataset muy pequeño).")
        return {}

    logger.info(f"=== Benchmark walk-forward: {len(splits)} folds, {len(MODELS)} modelos ===")
    results = {name: {"fold_results": []} for name in MODELS}

    for fold_idx, ((X_tr, y_tr), (X_te, y_te)) in enumerate(splits):
        logger.info(f"Fold {fold_idx+1}/{len(splits)} — train={len(X_tr)}, test={len(X_te)}, "
                    f"positivos_test={int(y_te.sum())}")
        for name, model_fn in MODELS.items():
            t0 = time.time()
            model = model_fn()
            model.fit(X_tr, y_tr)
            elapsed = time.time() - t0

            y_pred = model.predict(X_te)
            y_prob = model.predict_proba(X_te)[:, 1]
            m = _compute_metrics(y_te, y_pred, y_prob, elapsed, fold_idx + 1)
            results[name]["fold_results"].append(m)
            logger.info(f"  {name:4s}: acc={m['accuracy']:.3f}  f1={m['f1']:.3f}  "
                        f"auc={m['roc_auc']:.3f}  ({elapsed:.1f}s)")

    # Promedios por modelo
    logger.info("=== Resultados finales benchmark ===")
    for name in MODELS:
        folds = results[name]["fold_results"]
        if not folds:
            continue
        mean = {
            k: float(np.mean([f[k] for f in folds]))
            for k in ["accuracy", "precision", "recall", "f1", "roc_auc"]
        }
        results[name]["mean_metrics"] = mean
        logger.info(f"  {name.upper():4s} → mean_f1={mean['f1']:.4f}  "
                    f"mean_auc={mean['roc_auc']:.4f}  mean_recall={mean['recall']:.4f}")

    return results
