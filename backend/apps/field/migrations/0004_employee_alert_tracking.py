"""Migration 0004 — alert tracking fields on Employee."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("field", "0003_refuge_point"),
    ]

    operations = [
        migrations.AddField(
            model_name="employee",
            name="last_alert_level",
            field=models.PositiveSmallIntegerField(
                blank=True,
                null=True,
                help_text="Último nivel de alerta enviado por FCM (1=Verde 2=Amarillo 3=Naranja 4=Rojo)",
            ),
        ),
        migrations.AddField(
            model_name="employee",
            name="last_alert_sent_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text="Momento en que se envió el último push de alerta al dispositivo",
            ),
        ),
    ]
