"""Tareas Celery de weather — notificación de alertas de tormenta."""
import logging
from django.utils import timezone
from celery import shared_task

logger = logging.getLogger("weather.tasks")

LEVEL_LABELS = {1: "Verde", 2: "Amarillo", 3: "Naranja", 4: "Rojo"}
LEVEL_COLORS = {1: "#22c55e", 2: "#eab308", 3: "#f97316", 4: "#ef4444"}

NOTIFY_FROM_LEVEL = 2  # Notifica desde nivel 2 (Amarillo) en adelante


@shared_task(name="weather.notify_pending_alerts")
def notify_pending_alerts():
    """Revisa StormAlerts sin notificar y envía email/notificación interna."""
    from apps.weather.models import StormAlert
    from apps.notifications.utils import send_notification
    from apps.users.models import CustomUser

    pending = StormAlert.objects.filter(
        notified_at__isnull=True,
        is_active=True,
        alert_level__gte=NOTIFY_FROM_LEVEL,
    ).select_related("station")

    if not pending.exists():
        return

    superusers = list(CustomUser.objects.filter(is_active=True, is_superuser=True).values_list("id", flat=True))

    now = timezone.now()
    notified_count = 0

    for alert in pending:
        level_label = LEVEL_LABELS.get(alert.alert_level, str(alert.alert_level))
        color = LEVEL_COLORS.get(alert.alert_level, "#6b7280")
        station = alert.station

        title = f"⚡ Alerta {level_label} — {station.name}"
        body = (
            f"Estación: {station.name} ({station.department})\n"
            f"Probabilidad: {alert.probability:.0%}\n"
            f"Nivel: {alert.alert_level} — {level_label}\n"
            f"Generado: {alert.generated_at.strftime('%Y-%m-%d %H:%M UTC')}"
        )

        for user_id in superusers:
            try:
                send_notification(user_id=user_id, title=title, body=body)
            except Exception as exc:
                logger.error(f"Error notificando user {user_id}: {exc}")

        if alert.alert_level >= 3:
            _send_alert_email(alert, level_label)

        alert.notified_at = now
        alert.save(update_fields=["notified_at"])
        notified_count += 1
        logger.info(f"Alerta notificada: {station.code} nivel={alert.alert_level} prob={alert.probability:.3f}")

    logger.info(f"notify_pending_alerts: {notified_count} alertas procesadas")


def _send_alert_email(alert, level_label: str):
    """Envía email de alerta a superusuarios (solo nivel Naranja/Rojo)."""
    from django.core.mail import EmailMultiAlternatives
    from django.conf import settings
    from apps.users.models import CustomUser

    recipients = list(
        CustomUser.objects.filter(is_active=True, is_superuser=True).values_list("email", flat=True)
    )
    if not recipients:
        return

    station = alert.station
    subject = f"[Ximbra] Alerta Nivel {alert.alert_level} {level_label} — {station.name}"
    text_body = (
        f"ALERTA DE TORMENTA ELÉCTRICA\n\n"
        f"Estación: {station.name}\n"
        f"Departamento: {station.department}\n"
        f"Probabilidad: {alert.probability:.0%}\n"
        f"Nivel: {alert.alert_level} — {level_label}\n"
        f"Generado: {alert.generated_at.strftime('%Y-%m-%d %H:%M UTC')}\n"
        f"Modelo: {alert.model_version}\n\n"
        f"Sistema Ximbra — Alertas de Tormentas Eléctricas"
    )
    html_body = f"""
    <div style="font-family:sans-serif;max-width:560px;margin:0 auto;padding:24px">
      <h2 style="color:#1f2937">⚡ Alerta de Tormenta Eléctrica</h2>
      <div style="background:{LEVEL_COLORS.get(alert.alert_level,'#6b7280')};
                  color:#fff;padding:12px 20px;border-radius:8px;margin:16px 0">
        <strong>Nivel {alert.alert_level} — {level_label}</strong>
        &nbsp;|&nbsp; Probabilidad: <strong>{alert.probability:.0%}</strong>
      </div>
      <table style="width:100%;border-collapse:collapse;font-size:14px">
        <tr><td style="padding:6px 0;color:#6b7280">Estación</td>
            <td style="padding:6px 0"><strong>{station.name}</strong></td></tr>
        <tr><td style="padding:6px 0;color:#6b7280">Departamento</td>
            <td style="padding:6px 0">{station.department}</td></tr>
        <tr><td style="padding:6px 0;color:#6b7280">Generado</td>
            <td style="padding:6px 0">{alert.generated_at.strftime('%Y-%m-%d %H:%M UTC')}</td></tr>
        <tr><td style="padding:6px 0;color:#6b7280">Modelo</td>
            <td style="padding:6px 0">{alert.model_version}</td></tr>
      </table>
      <hr style="border:none;border-top:1px solid #e5e7eb;margin:20px 0">
      <p style="font-size:12px;color:#9ca3af">Ximbra — Sistema de Alertas de Tormentas</p>
    </div>
    """
    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipients,
        )
        msg.attach_alternative(html_body, "text/html")
        msg.send()
        logger.info(f"Email de alerta enviado a {recipients}")
    except Exception as exc:
        logger.error(f"Error enviando email de alerta: {exc}")
