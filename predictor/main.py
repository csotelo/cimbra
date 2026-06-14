"""Ximbra Predictor — inferencia horaria: observación nueva → StormAlert en BD."""
import logging
import os
import signal
import time

from dotenv import load_dotenv

from app.application.predict import PredictUseCase
from app.infrastructure.postgres import PostgresAdapter

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("predictor")

DB_URL = os.environ["DB_URL"]
CYCLE_INTERVAL = int(os.environ.get("MIN_CYCLE_INTERVAL_SEC", "3600"))

running = True


def stop(sig, frame):
    global running
    logger.info("Deteniendo predictor...")
    running = False


signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)


def main():
    db = PostgresAdapter(DB_URL)
    db.connect()

    use_case = PredictUseCase(db)
    logger.info(f"Predictor iniciado — ciclo cada {CYCLE_INTERVAL}s")

    while running:
        try:
            if not db.ping():
                logger.warning("Reconectando a PostgreSQL...")
                db.reconnect()
            use_case.execute()
        except Exception as exc:
            logger.error(f"Error en ciclo predictor: {exc}", exc_info=True)

        elapsed = 0
        while running and elapsed < CYCLE_INTERVAL:
            time.sleep(5)
            elapsed += 5

    db.close()
    logger.info("Predictor detenido.")


if __name__ == "__main__":
    main()
