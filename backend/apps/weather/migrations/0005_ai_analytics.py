import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("weather", "0004_telegram"),
    ]

    operations = [
        # ModelArtifact: métricas avanzadas + configuración IA
        migrations.AddField(model_name="modelartifact", name="f1",
            field=models.FloatField(blank=True, null=True)),
        migrations.AddField(model_name="modelartifact", name="roc_auc",
            field=models.FloatField(blank=True, null=True)),
        migrations.AddField(model_name="modelartifact", name="best_model_type",
            field=models.CharField(blank=True, default="mlp", max_length=20)),
        migrations.AddField(model_name="modelartifact", name="model_type",
            field=models.CharField(blank=True, default="mlp", max_length=20)),
        migrations.AddField(model_name="modelartifact", name="feature_importance_json",
            field=models.JSONField(blank=True, null=True)),
        migrations.AddField(model_name="modelartifact", name="shap_background_path",
            field=models.CharField(blank=True, default="", max_length=255)),
        migrations.AddField(model_name="modelartifact", name="calibrator_path",
            field=models.CharField(blank=True, default="", max_length=255)),
        migrations.AddField(model_name="modelartifact", name="thresholds_json",
            field=models.JSONField(blank=True, null=True)),
        # StormAlert: explicabilidad SHAP por predicción
        migrations.AddField(model_name="stormalert", name="explanation_json",
            field=models.JSONField(blank=True, null=True)),
        # ModelBenchmark: resultados del benchmark multi-modelo
        migrations.CreateModel(
            name="ModelBenchmark",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("model_type", models.CharField(max_length=20)),
                ("cv_fold", models.IntegerField()),
                ("accuracy", models.FloatField(default=0)),
                ("precision", models.FloatField(default=0)),
                ("recall", models.FloatField(default=0)),
                ("f1", models.FloatField(default=0)),
                ("roc_auc", models.FloatField(default=0)),
                ("training_seconds", models.FloatField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("artifact", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="benchmarks",
                    to="weather.modelartifact",
                )),
            ],
            options={"db_table": "model_benchmarks", "ordering": ["-created_at"]},
        ),
    ]
