from rest_framework import serializers

from .models import ModelArtifact, Station, StormAlert, TelegramSubscription, WeatherObservation


class StationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Station
        fields = ["id", "code", "name", "department", "latitude", "longitude", "altitude_m", "is_active"]


class WeatherObservationSerializer(serializers.ModelSerializer):
    station_code = serializers.CharField(source="station.code", read_only=True)

    class Meta:
        model = WeatherObservation
        fields = ["id", "station", "station_code", "observed_at", "temperature", "humidity", "pressure", "cape", "k_index", "source", "ingested_at"]


class StormAlertSerializer(serializers.ModelSerializer):
    station_code = serializers.CharField(source="station.code", read_only=True)
    station_name = serializers.CharField(source="station.name", read_only=True)
    department = serializers.CharField(source="station.department", read_only=True)
    level_label = serializers.CharField(source="get_alert_level_display", read_only=True)

    class Meta:
        model = StormAlert
        fields = [
            "id", "station", "station_code", "station_name", "department",
            "probability", "alert_level", "level_label", "is_active",
            "generated_at", "model_version", "created_at",
        ]


class TelegramSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelegramSubscription
        fields = ["id", "chat_id", "username", "department", "min_level", "is_active", "created_at"]
