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
