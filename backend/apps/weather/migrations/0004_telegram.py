from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("weather", "0003_stormalert_notified_at"),
    ]

    operations = [
        migrations.AddField(
            model_name="stormalert",
            name="telegram_notified_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name="TelegramSubscription",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("chat_id", models.BigIntegerField(unique=True)),
                ("username", models.CharField(blank=True, default="", max_length=150)),
                ("department", models.CharField(blank=True, default="", max_length=100,
                                                help_text="Vacío = todos los departamentos")),
                ("min_level", models.IntegerField(default=2,
                                                  help_text="Nivel mínimo de alerta a notificar (1-4)")),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": "telegram_subscriptions", "ordering": ["-created_at"]},
        ),
    ]
