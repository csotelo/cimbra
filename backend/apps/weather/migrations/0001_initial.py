from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Station",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=20, unique=True)),
                ("name", models.CharField(max_length=100)),
                ("department", models.CharField(max_length=100)),
                ("latitude", models.DecimalField(decimal_places=6, max_digits=9)),
                ("longitude", models.DecimalField(decimal_places=6, max_digits=9)),
                ("altitude_m", models.IntegerField(blank=True, null=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": "weather_stations", "ordering": ["department", "name"]},
        ),
        migrations.CreateModel(
            name="WeatherObservation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("observed_at", models.DateTimeField(db_index=True)),
                ("temperature", models.FloatField(blank=True, null=True)),
                ("humidity", models.FloatField(blank=True, null=True)),
                ("pressure", models.FloatField(blank=True, null=True)),
                ("cape", models.FloatField(blank=True, null=True)),
                ("k_index", models.FloatField(blank=True, null=True)),
                ("source", models.CharField(default="open-meteo", max_length=50)),
                ("raw_data", models.JSONField(default=dict)),
                ("ingested_at", models.DateTimeField(auto_now_add=True)),
                ("station", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="observations", to="weather.station")),
            ],
            options={"db_table": "weather_observations", "ordering": ["-observed_at"]},
        ),
        migrations.CreateModel(
            name="StormAlert",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("probability", models.FloatField()),
                ("alert_level", models.IntegerField(choices=[(1, "Verde — Sin riesgo"), (2, "Amarillo — Moderado"), (3, "Naranja — Peligroso"), (4, "Rojo — Extremo")])),
                ("is_active", models.BooleanField(default=True)),
                ("generated_at", models.DateTimeField(db_index=True)),
                ("model_version", models.CharField(default="", max_length=50)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("station", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="alerts", to="weather.station")),
                ("observation", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="weather.weatherobservation")),
            ],
            options={"db_table": "storm_alerts", "ordering": ["-generated_at"]},
        ),
        migrations.AddIndex(
            model_name="weatherobservation",
            index=models.Index(fields=["station", "observed_at"], name="weather_obs_station_obs_idx"),
        ),
        migrations.AlterUniqueTogether(
            name="weatherobservation",
            unique_together={("station", "observed_at")},
        ),
        migrations.AddIndex(
            model_name="stormalert",
            index=models.Index(fields=["station", "generated_at"], name="storm_alert_station_gen_idx"),
        ),
        migrations.AddIndex(
            model_name="stormalert",
            index=models.Index(fields=["alert_level", "is_active"], name="storm_alert_level_active_idx"),
        ),
    ]
