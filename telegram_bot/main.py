"""Ximbra Telegram Bot — alertas de tormenta + suscripciones por departamento.

Dos loops paralelos (asyncio):
  1. Bot polling — recibe comandos /start /alertas /suscribir /estado /cancelar
  2. Notifier loop — revisa storm_alerts pendientes y envía a suscriptores
"""
import asyncio
import logging
import os
import signal

from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler

from app.application.handlers import (
    cmd_alertas,
    cmd_cancelar,
    cmd_estado,
    cmd_start,
    cmd_suscribir,
)
from app.application.notifier import dispatch_pending_alerts
from app.infrastructure.postgres import PostgresAdapter

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("telegram_bot")

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
DB_URL = os.environ["DB_URL"]
NOTIFIER_INTERVAL = int(os.environ.get("MIN_CYCLE_INTERVAL_SEC", "300"))

running = True


async def notifier_loop(bot, db: PostgresAdapter):
    logger.info(f"Notifier loop iniciado — ciclo cada {NOTIFIER_INTERVAL}s")
    while running:
        try:
            if not db.ping():
                logger.warning("Reconectando a PostgreSQL...")
                db.reconnect()
            await dispatch_pending_alerts(db, bot)
        except Exception as exc:
            logger.error(f"Error en notifier loop: {exc}", exc_info=True)
        await asyncio.sleep(NOTIFIER_INTERVAL)


async def main():
    global running

    db = PostgresAdapter(DB_URL)
    db.connect()
    logger.info("PostgreSQL conectado")

    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .build()
    )
    app.bot_data["db"] = db

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("alertas", cmd_alertas))
    app.add_handler(CommandHandler("suscribir", cmd_suscribir))
    app.add_handler(CommandHandler("estado", cmd_estado))
    app.add_handler(CommandHandler("cancelar", cmd_cancelar))

    loop = asyncio.get_event_loop()

    def stop():
        global running
        running = False
        logger.info("Deteniendo bot...")

    loop.add_signal_handler(signal.SIGTERM, stop)
    loop.add_signal_handler(signal.SIGINT, stop)

    async with app:
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        logger.info("Bot Telegram activo — escuchando comandos")

        await notifier_loop(app.bot, db)

        await app.updater.stop()
        await app.stop()

    db.close()
    logger.info("Bot detenido.")


if __name__ == "__main__":
    asyncio.run(main())
