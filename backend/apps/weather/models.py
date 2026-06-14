import uuid

from django.db import models


class Station(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    altitude_m = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "weather_stations"
        ordering = ["department", "name"]

    def __str__(self):
        return f"{self.code} — {self.name} ({self.department})"


class WeatherObservation(models.Model):
    station = models.ForeignKey(
        Station, on_delete=models.CASCADE, related_name="observations"
    )
    observed_at = models.DateTimeField(db_index=True)
    temperature = models.FloatField(null=True, blank=True)
    humidity = models.FloatField(null=True, blank=True)
    pressure = models.FloatField(null=True, blank=True)
    cape = models.FloatField(null=True, blank=True)
    k_index = models.FloatField(null=True, blank=True)
    source = models.CharField(max_length=50, default="open-meteo")
    raw_data = models.JSONField(default=dict)
    ingested_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "weather_observations"
        unique_together = [("station", "observed_at")]
        ordering = ["-observed_at"]
        indexes = [
            models.Index(fields=["station", "observed_at"]),
        ]

    def __str__(self):
        return f"{self.station.code} @ {self.observed_at:%Y-%m-%d %H:%M}"


class StormAlert(models.Model):
    class Level(models.IntegerChoices):
        VERDE = 1, "Verde — Sin riesgo"
        AMARILLO = 2, "Amarillo — Moderado"
        NARANJA = 3, "Naranja — Peligroso"
        ROJO = 4, "Rojo — Extremo"

    LEVEL_COLORS = {1: "#22c55e", 2: "#eab308", 3: "#f97316", 4: "#ef4444"}

    station = models.ForeignKey(
        Station, on_delete=models.CASCADE, related_name="alerts"
    )
    observation = models.ForeignKey(
        WeatherObservation, on_delete=models.SET_NULL, null=True, blank=True
    )
    probability = models.FloatField()
    alert_level = models.IntegerField(choices=Level.choices)
    is_active = models.BooleanField(default=True)
    generated_at = models.DateTimeField(db_index=True)
    model_version = models.CharField(max_length=50, default="")
    notified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "storm_alerts"
        ordering = ["-generated_at"]
        indexes = [
            models.Index(fields=["station", "generated_at"]),
            models.Index(fields=["alert_level", "is_active"]),
        ]

    def __str__(self):
        return f"[Nivel {self.alert_level}] {self.station.code} — {self.probability:.0%} @ {self.generated_at:%Y-%m-%d %H:%M}"


class ModelArtifact(models.Model):
    class Status(models.TextChoices):
        TRAINING = "training", "Entrenando"
        READY = "ready", "Listo"
        FAILED = "failed", "Fallido"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    version = models.CharField(max_length=50, unique=True)
    model_path = models.CharField(max_length=255)
    scaler_path = models.CharField(max_length=255, default="")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.TRAINING)
    samples_train = models.IntegerField(default=0)
    samples_val = models.IntegerField(default=0)
    samples_test = models.IntegerField(default=0)
    accuracy = models.FloatField(null=True, blank=True)
    precision = models.FloatField(null=True, blank=True)
    recall = models.FloatField(null=True, blank=True)
    loss = models.FloatField(null=True, blank=True)
    epochs_run = models.IntegerField(default=0)
    training_seconds = models.IntegerField(default=0)
    is_active = models.BooleanField(default=False)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "model_artifacts"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.version} [{self.status}] acc={self.accuracy:.3f}" if self.accuracy else f"{self.version} [{self.status}]"
