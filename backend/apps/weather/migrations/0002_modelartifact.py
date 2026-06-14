import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("weather", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ModelArtifact",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("version", models.CharField(max_length=50, unique=True)),
                ("model_path", models.CharField(max_length=255)),
                ("scaler_path", models.CharField(default="", max_length=255)),
                ("status", models.CharField(choices=[("training", "Entrenando"), ("ready", "Listo"), ("failed", "Fallido")], default="training", max_length=20)),
                ("samples_train", models.IntegerField(default=0)),
                ("samples_val", models.IntegerField(default=0)),
                ("samples_test", models.IntegerField(default=0)),
                ("accuracy", models.FloatField(blank=True, null=True)),
                ("precision", models.FloatField(blank=True, null=True)),
                ("recall", models.FloatField(blank=True, null=True)),
                ("loss", models.FloatField(blank=True, null=True)),
                ("epochs_run", models.IntegerField(default=0)),
                ("training_seconds", models.IntegerField(default=0)),
                ("is_active", models.BooleanField(default=False)),
                ("notes", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": "model_artifacts", "ordering": ["-created_at"]},
        ),
    ]
