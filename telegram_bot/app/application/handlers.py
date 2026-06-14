"""Handlers de comandos Telegram."""
import logging

from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger("telegram_bot.handlers")

LEVEL_LABELS = {1: "🟢 Verde", 2: "🟡 Amarillo", 3: "🟠 Naranja", 4: "🔴 Rojo"}

DEPARTMENTS = [
    "Lima", "Cusco", "Arequipa", "Loreto", "Piura",
    "Junín", "Puno", "Cajamarca", "Huánuco", "Tumbes",
]


def _db(context: ContextTypes.DEFAULT_TYPE):
    return context.application.bot_data["db"]


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    username = update.effective_user.username or ""
    db = _db(context)

    sub = db.get_subscription(chat_id)
    if sub and sub["is_active"]:
        dept = sub["department"] or "todos los departamentos"
        await update.message.reply_text(
            f"✅ Ya estás suscrito a alertas de *{dept}* (nivel ≥ {sub['min_level']}).\n\n"
            f"Comandos disponibles:\n"
            f"/alertas — ver alertas activas\n"
            f"/suscribir — cambiar suscripción\n"
            f"/estado — tu configuración actual\n"
            f"/cancelar — cancelar suscripción",
            parse_mode="Markdown",
        )
        return

    db.upsert_subscription(chat_id=chat_id, username=username)
    await update.message.reply_text(
        "⚡ *Bienvenido a Ximbra — Alertas de Tormentas Eléctricas*\n\n"
        "Estás suscrito a alertas de nivel ≥ 2 (Amarillo) para *todos los departamentos*.\n\n"
        "Comandos:\n"
        "/alertas — ver alertas activas ahora\n"
        "/suscribir <departamento> — filtrar por departamento\n"
        "/suscribir <departamento> <nivel> — filtrar por depto y nivel mínimo (1-4)\n"
        "/estado — ver tu suscripción\n"
        "/cancelar — cancelar suscripción\n\n"
        f"Departamentos disponibles: {', '.join(DEPARTMENTS)}",
        parse_mode="Markdown",
    )


async def cmd_alertas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = _db(context)
    alerts = db.get_active_alerts_summary()

    if not alerts:
        await update.message.reply_text("✅ Sin alertas activas en este momento.")
        return

    lines = ["⚡ *Alertas activas:*\n"]
    for a in alerts:
        label = LEVEL_LABELS.get(a["alert_level"], str(a["alert_level"]))
        lines.append(f"{label} *{a['station_name']}* ({a['department']}) — {a['probability']*100:.1f}%")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_suscribir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    username = update.effective_user.username or ""
    db = _db(context)
    args = context.args or []

    department = ""
    min_level = 2

    if args:
        department = args[0].capitalize()
        if department not in DEPARTMENTS:
            await update.message.reply_text(
                f"❌ Departamento no reconocido: *{department}*\n\n"
                f"Disponibles: {', '.join(DEPARTMENTS)}",
                parse_mode="Markdown",
            )
            return
    if len(args) >= 2:
        try:
            min_level = int(args[1])
            if min_level not in range(1, 5):
                raise ValueError
        except ValueError:
            await update.message.reply_text("❌ Nivel debe ser un número entre 1 y 4.")
            return

    db.upsert_subscription(chat_id=chat_id, username=username, department=department, min_level=min_level)
    dept_txt = department or "todos los departamentos"
    await update.message.reply_text(
        f"✅ Suscripción actualizada:\n"
        f"📍 Departamento: *{dept_txt}*\n"
        f"🔔 Nivel mínimo: *{min_level}* ({LEVEL_LABELS.get(min_level, '')})",
        parse_mode="Markdown",
    )


async def cmd_estado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    db = _db(context)
    sub = db.get_subscription(chat_id)

    if not sub or not sub["is_active"]:
        await update.message.reply_text(
            "❌ No tienes suscripción activa.\nUsa /start para suscribirte."
        )
        return

    dept = sub["department"] or "todos los departamentos"
    await update.message.reply_text(
        f"📋 *Tu suscripción:*\n\n"
        f"👤 @{sub['username'] or 'sin username'}\n"
        f"📍 Departamento: *{dept}*\n"
        f"🔔 Nivel mínimo: *{sub['min_level']}* ({LEVEL_LABELS.get(sub['min_level'], '')})\n"
        f"✅ Activa desde: {sub['created_at'].strftime('%Y-%m-%d')}",
        parse_mode="Markdown",
    )


async def cmd_cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    db = _db(context)
    db.deactivate_subscription(chat_id)
    await update.message.reply_text(
        "🔕 Suscripción cancelada. Ya no recibirás alertas.\n"
        "Usa /start para volver a suscribirte."
    )
