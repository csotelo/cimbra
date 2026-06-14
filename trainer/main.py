"""Ximbra Trainer — pipeline CRISP-DM completo con IA analítica avanzada.

Fases:
  1. Backfill histórico (Open-Meteo Archive)
  2. Preparación y limpieza del dataset
  3. Benchmark multi-modelo walk-forward CV (MLP sklearn, RF, XGBoost)   [v0.6.0]
  4. Entrenamiento MLP Keras (modelo base de tesis)
  5. Entrenamiento LSTM Keras (ventana temporal 6h)                       [v0.7.0]
  6. Selección del mejor modelo neuronal por ROC-AUC en test
  7. XAI: SHAP feature importance global + background para predictor      [v0.8.0]
  8. Calibración Platt Scaling + umbrales SENAMHI óptimos                 [v0.9.0]
  9. Registro y activación del artefacto en BD

Corre UNA VEZ y sale (restart: "no" en docker-compose).
Para reentrenar: docker compose run --rm trainer
"""
import logging
import os
import sys
from datetime import datetime

import numpy as np
from dotenv import load_dotenv

from app.application.benchmark import run_benchmark
from app.application.calibrate import calibrate_and_compute_thresholds
from app.application.explain import (compute_global_importance,
                                      save_shap_background)
from app.application.fetch_history import backfill_if_needed
from app.application.prepare import create_sequences, prepare_dataset
from app.application.train import train_lstm, train_model
from app.infrastructure.postgres import PostgresAdapter

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("trainer")

DB_URL = os.environ["DB_URL"]
MODEL_DIR = os.environ.get("MODEL_PATH", "/models")
os.makedirs(MODEL_DIR, exist_ok=True)


def main():
    version = datetime.utcnow().strftime("v%Y%m%d_%H%M%S")
    mlp_path = f"{MODEL_DIR}/storm_model_mlp_{version}.keras"
    lstm_path = f"{MODEL_DIR}/storm_model_lstm_{version}.keras"
    scaler_path = f"{MODEL_DIR}/scaler_{version}.joblib"
    shap_bg_path = f"{MODEL_DIR}/shap_bg_{version}.npy"
    calibrator_path = f"{MODEL_DIR}/calibrator_{version}.joblib"

    logger.info(f"=== Trainer Ximbra — {version} ===")

    db = PostgresAdapter(DB_URL)
    db.connect()

    try:
        # ── Fase 1: Backfill histórico ──────────────────────────────────────
        total = backfill_if_needed(db)
        if total < 100:
            logger.error("Sin datos suficientes para entrenar (mínimo 100 obs con CAPE y K-Index).")
            sys.exit(1)

        logger.info("Cargando dataset desde BD...")
        records = db.load_dataset()
        logger.info(f"Dataset cargado: {len(records)} registros")

        # Registrar artefacto (estado inicial: training)
        artifact_id = db.create_artifact(version, mlp_path, scaler_path)

        try:
            # ── Fase 2: Preparación ─────────────────────────────────────────
            X_train, X_val, X_test, y_train, y_val, y_test, n_tr, n_va, n_te = prepare_dataset(
                records, scaler_path
            )
            db.update_artifact(artifact_id, samples_train=n_tr, samples_val=n_va, samples_test=n_te)

            X_all = np.vstack([X_train, X_val, X_test])
            y_all = np.concatenate([y_train, y_val, y_test])

            # ── Fase 3 [v0.6.0]: Benchmark multi-modelo walk-forward CV ────
            logger.info("=== FASE 3: Benchmark multi-modelo (walk-forward CV) ===")
            bench = run_benchmark(X_all, y_all, n_splits=4)
            for mtype, res in bench.items():
                for fold in res.get("fold_results", []):
                    db.save_benchmark(artifact_id, mtype, fold["cv_fold"], fold)

            best_bench = ""
            if bench:
                best_bench = max(bench.items(), key=lambda kv: kv[1].get("mean_metrics", {}).get("f1", 0))[0]
                logger.info(f"Mejor en benchmark (mean F1): {best_bench.upper()}")
                db.update_artifact(artifact_id, best_model_type=best_bench)

            # ── Fase 4: Entrenamiento MLP Keras ────────────────────────────
            logger.info("=== FASE 4: Entrenamiento MLP Keras ===")
            mlp_metrics = train_model(X_train, X_val, X_test, y_train, y_val, y_test, mlp_path)

            # ── Fase 5 [v0.7.0]: Entrenamiento LSTM Keras ──────────────────
            logger.info("=== FASE 5: Entrenamiento LSTM Keras (ventana 6h) ===")
            X_tr_seq, y_tr_seq = create_sequences(X_train, y_train)
            X_va_seq, y_va_seq = create_sequences(X_val, y_val)
            X_te_seq, y_te_seq = create_sequences(X_test, y_test)

            lstm_metrics = None
            if len(X_tr_seq) >= 50 and len(X_te_seq) >= 10:
                lstm_metrics = train_lstm(
                    X_tr_seq, X_va_seq, X_te_seq,
                    y_tr_seq, y_va_seq, y_te_seq,
                    lstm_path,
                )
            else:
                logger.warning(f"Dataset insuficiente para LSTM ({len(X_tr_seq)} secuencias). Usando solo MLP.")

            # ── Selección: MLP vs LSTM por ROC-AUC ─────────────────────────
            if lstm_metrics and lstm_metrics["roc_auc"] > mlp_metrics["roc_auc"]:
                best_metrics = lstm_metrics
                best_model_path = lstm_path
                best_model_type = "lstm"
                logger.info(f"LSTM seleccionado (auc={lstm_metrics['roc_auc']:.4f} > mlp={mlp_metrics['roc_auc']:.4f})")
            else:
                best_metrics = mlp_metrics
                best_model_path = mlp_path
                best_model_type = "mlp"
                logger.info(f"MLP seleccionado (auc={mlp_metrics['roc_auc']:.4f})")

            # Actualizar ruta del modelo ganador en artefacto
            db.update_artifact(artifact_id, model_path=best_model_path, model_type=best_model_type)

            # ── Fase 6 [v0.8.0]: SHAP explainability ───────────────────────
            logger.info("=== FASE 6: SHAP feature importance global ===")
            import tensorflow as tf
            best_model = tf.keras.models.load_model(best_model_path)

            X_train_for_shap = X_tr_seq if best_model_type == "lstm" else X_train
            X_test_for_shap = X_te_seq if best_model_type == "lstm" else X_test

            importance = compute_global_importance(best_model, X_train_for_shap,
                                                    X_test_for_shap, model_type=best_model_type)
            save_shap_background(X_train_for_shap, shap_bg_path)
            db.update_artifact(artifact_id,
                               feature_importance_json=importance,
                               shap_background_path=shap_bg_path)

            # ── Fase 7 [v0.9.0]: Calibración Platt Scaling ─────────────────
            logger.info("=== FASE 7: Calibración Platt Scaling + umbrales SENAMHI ===")
            X_val_cal = X_va_seq if best_model_type == "lstm" else X_val
            y_val_cal = y_va_seq if best_model_type == "lstm" else y_val

            thresholds = calibrate_and_compute_thresholds(
                best_model, X_val_cal, y_val_cal, calibrator_path
            )
            db.update_artifact(artifact_id,
                               calibrator_path=calibrator_path,
                               thresholds_json=thresholds)

            # ── Activar artefacto ───────────────────────────────────────────
            db.update_artifact(artifact_id, status="ready", **best_metrics)
            db.activate_artifact(artifact_id)

            logger.info("=== Entrenamiento Ximbra completado ===")
            logger.info(f"  Versión:       {version}")
            logger.info(f"  Modelo:        {best_model_type.upper()}")
            logger.info(f"  Accuracy:      {best_metrics['accuracy']:.4f}")
            logger.info(f"  F1:            {best_metrics['f1']:.4f}")
            logger.info(f"  ROC-AUC:       {best_metrics['roc_auc']:.4f}")
            logger.info(f"  Precision:     {best_metrics['precision']:.4f}")
            logger.info(f"  Recall:        {best_metrics['recall']:.4f}")
            logger.info(f"  Épocas:        {best_metrics['epochs_run']}")
            logger.info(f"  Tiempo total:  {best_metrics['training_seconds']}s")
            logger.info(f"  Umbrales cal.: {thresholds}")
            logger.info(f"  SHAP top feat: {sorted(importance.items(), key=lambda x: x[1], reverse=True)[0]}")
            logger.info(f"  Modelo path:   {best_model_path}")

        except Exception as exc:
            logger.error(f"Error durante pipeline: {exc}", exc_info=True)
            db.update_artifact(artifact_id, status="failed", notes=str(exc)[:500])
            sys.exit(1)

    finally:
        db.close()


if __name__ == "__main__":
    main()
