"""Loop de notificación: revisa alertas pendientes y las envía a suscriptores."""
import logging

logger = logging.getLogger("telegram_bot.notifier")

LEVEL_LABELS = {1: "🟢 Verde", 2: "🟡 Amarillo", 3: "🟠 Naranja", 4: "🔴 Rojo"}
LEVEL_EMOJI  = {1: "🟢", 2: "🟡", 3: "🟠", 4: "🔴"}


def format_alert_message(alert: dict) -> str:
    level = alert["alert_level"]
    prob = alert["probability"] * 100
    return (
        f"⚡ *ALERTA DE TORMENTA ELÉCTRICA*\n\n"
        f"{LEVEL_EMOJI.get(level, '⚠️')} *Nivel {level} — {LEVEL_LABELS.get(level, '')}*\n"
        f"📍 *{alert['station_name']}* ({alert['department']})\n"
        f"📊 Probabilidad: *{prob:.1f}%*\n"
        f"🕐 {alert['generated_at'].strftime('%Y-%m-%d %H:%M UTC')}\n"
        f"🤖 Modelo: `{alert['model_version']}`\n\n"
        f"_Sistema Ximbra — Alertas de Tormentas_"
    )


async def dispatch_pending_alerts(db, bot):
    alerts = db.get_pending_telegram_alerts()
    if not alerts:
        return

    notified_ids = []

    for alert in alerts:
        subscribers = db.get_subscribers_for_alert(
            department=alert["department"],
            alert_level=alert["alert_level"],
        )
        if not subscribers:
            notified_ids.append(alert["id"])
            continue

        text = format_alert_message(alert)
        sent = 0
        for sub in subscribers:
            try:
                await bot.send_message(
                    chat_id=sub["chat_id"],
                    text=text,
                    parse_mode="Markdown",
                )
                sent += 1
            except Exception as exc:
                logger.warning(f"Error enviando a {sub['chat_id']}: {exc}")

        notified_ids.append(alert["id"])
        logger.info(
            f"Alerta {alert['station_code']} nivel={alert['alert_level']} "
            f"prob={alert['probability']:.3f} → {sent}/{len(subscribers)} enviados"
        )

    db.mark_telegram_notified(notified_ids)
