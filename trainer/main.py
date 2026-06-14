"""Ximbra Trainer — pipeline CRISP-DM completo: backfill → preparación → entrenamiento → artefacto.

Corre UNA VEZ y sale (restart: "no" en docker-compose).
Para reentrenar: docker compose run --rm trainer
"""
import logging
import os
import sys
from datetime import datetime

from dotenv import load_dotenv

from app.application.fetch_history import backfill_if_needed
from app.application.prepare import prepare_dataset
from app.application.train import train_model
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
    model_path = f"{MODEL_DIR}/storm_model_{version}.keras"
    scaler_path = f"{MODEL_DIR}/scaler_{version}.joblib"

    logger.info(f"=== Trainer Ximbra — {version} ===")

    db = PostgresAdapter(DB_URL)
    db.connect()

    try:
        # CRISP-DM Fase 2-3: Comprensión y preparación de datos
        total = backfill_if_needed(db)
        if total < 100:
            logger.error("Sin datos suficientes para entrenar. Asegúrate de tener estaciones activas.")
            sys.exit(1)

        # Cargar dataset de BD
        logger.info("Cargando dataset desde BD...")
        records = db.load_dataset()
        logger.info(f"Dataset cargado: {len(records)} registros")

        # Registrar artefacto en BD (estado: training)
        artifact_id = db.create_artifact(version, model_path, scaler_path)

        try:
            # CRISP-DM Fase 3: Preparación
            X_train, X_val, X_test, y_train, y_val, y_test, n_train, n_val, n_test = prepare_dataset(
                records, scaler_path
            )
            db.update_artifact(artifact_id, samples_train=n_train, samples_val=n_val, samples_test=n_test)

            # CRISP-DM Fase 4-5: Modelado y Evaluación
            metrics = train_model(X_train, X_val, X_test, y_train, y_val, y_test, model_path)

            # Actualizar artefacto con métricas y activar
            db.update_artifact(artifact_id, status="ready", **metrics)
            db.activate_artifact(artifact_id)

            logger.info(f"=== Entrenamiento exitoso ===")
            logger.info(f"  Versión:   {version}")
            logger.info(f"  Accuracy:  {metrics['accuracy']:.4f}")
            logger.info(f"  Precision: {metrics['precision']:.4f}")
            logger.info(f"  Recall:    {metrics['recall']:.4f}")
            logger.info(f"  Loss:      {metrics['loss']:.4f}")
            logger.info(f"  Épocas:    {metrics['epochs_run']}")
            logger.info(f"  Tiempo:    {metrics['training_seconds']}s")
            logger.info(f"  Modelo:    {model_path}")

        except Exception as exc:
            logger.error(f"Error durante entrenamiento: {exc}", exc_info=True)
            db.update_artifact(artifact_id, status="failed", notes=str(exc))
            sys.exit(1)

    finally:
        db.close()


if __name__ == "__main__":
    main()
