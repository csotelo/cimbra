import uuid

from django.contrib.gis.db import models


class Station(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    location = models.PointField(geography=True, srid=4326)
    altitude_m = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "weather_stations"
        ordering = ["department", "name"]

    def __str__(self):
        return f"{self.code} — {self.name} ({self.department})"

    @property
    def latitude(self):
        return self.location.y if self.location else None

    @property
    def longitude(self):
        return self.location.x if self.location else None


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
    telegram_notified_at = models.DateTimeField(null=True, blank=True)
    explanation_json = models.JSONField(null=True, blank=True)
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
    f1 = models.FloatField(null=True, blank=True)
    roc_auc = models.FloatField(null=True, blank=True)
    loss = models.FloatField(null=True, blank=True)
    epochs_run = models.IntegerField(default=0)
    training_seconds = models.IntegerField(default=0)
    best_model_type = models.CharField(max_length=20, default="mlp", blank=True)
    model_type = models.CharField(max_length=20, default="mlp", blank=True)
    feature_importance_json = models.JSONField(null=True, blank=True)
    shap_background_path = models.CharField(max_length=255, default="", blank=True)
    calibrator_path = models.CharField(max_length=255, default="", blank=True)
    thresholds_json = models.JSONField(null=True, blank=True)
    is_active = models.BooleanField(default=False)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "model_artifacts"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.version} [{self.status}] acc={self.accuracy:.3f}" if self.accuracy else f"{self.version} [{self.status}]"


class ModelBenchmark(models.Model):
    artifact = models.ForeignKey(
        ModelArtifact, on_delete=models.CASCADE, related_name="benchmarks"
    )
    model_type = models.CharField(max_length=20)
    cv_fold = models.IntegerField()
    accuracy = models.FloatField(default=0)
    precision = models.FloatField(default=0)
    recall = models.FloatField(default=0)
    f1 = models.FloatField(default=0)
    roc_auc = models.FloatField(default=0)
    training_seconds = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "model_benchmarks"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.model_type} fold={self.cv_fold} f1={self.f1:.3f}"


class TelegramSubscription(models.Model):
    chat_id = models.BigIntegerField(unique=True)
    username = models.CharField(max_length=150, blank=True, default="")
    department = models.CharField(max_length=100, blank=True, default="",
                                  help_text="Vacío = todos los departamentos")
    min_level = models.IntegerField(default=2,
                                    help_text="Nivel mínimo de alerta a notificar (1-4)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "telegram_subscriptions"
        ordering = ["-created_at"]

    def __str__(self):
        dept = self.department or "todos"
        return f"@{self.username or self.chat_id} → {dept} (nivel≥{self.min_level})"
