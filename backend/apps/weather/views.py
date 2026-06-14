import json

from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Station, StormAlert, TelegramSubscription, WeatherObservation
from .serializers import (
    StationGeoSerializer,
    StationSerializer,
    StormAlertSerializer,
    TelegramSubscriptionSerializer,
    WeatherObservationSerializer,
)


class StationListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = StationSerializer
    queryset = Station.objects.filter(is_active=True)


class ObservationListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = WeatherObservationSerializer

    def get_queryset(self):
        qs = WeatherObservation.objects.select_related("station").order_by("-observed_at")
        station = self.request.query_params.get("station")
        if station:
            qs = qs.filter(station__code=station)
        return qs[:200]


class AlertListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = StormAlertSerializer

    def get_queryset(self):
        qs = StormAlert.objects.select_related("station").filter(is_active=True).order_by("-generated_at")
        level = self.request.query_params.get("level")
        if level:
            qs = qs.filter(alert_level=level)
        return qs[:100]


class TelegramSubscriptionListView(ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = TelegramSubscriptionSerializer
    queryset = TelegramSubscription.objects.filter(is_active=True).order_by("-created_at")


class StationGeoView(APIView):
    """GeoJSON FeatureCollection de todas las estaciones activas."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        stations = Station.objects.filter(is_active=True)
        serializer = StationGeoSerializer(stations, many=True)
        return Response(serializer.data)


class AlertGeoView(APIView):
    """GeoJSON FeatureCollection de alertas activas con nivel y probabilidad."""
    permission_classes = [IsAuthenticated]

    COLORS = {1: "#22c55e", 2: "#eab308", 3: "#f97316", 4: "#ef4444"}

    def get(self, request):
        alerts = (
            StormAlert.objects
            .select_related("station")
            .filter(is_active=True)
            .order_by("-generated_at")
        )
        features = []
        for alert in alerts:
            if not alert.station.location:
                continue
            features.append({
                "type": "Feature",
                "geometry": json.loads(alert.station.location.geojson),
                "properties": {
                    "id": alert.id,
                    "station_code": alert.station.code,
                    "station_name": alert.station.name,
                    "department": alert.station.department,
                    "altitude_m": alert.station.altitude_m,
                    "alert_level": alert.alert_level,
                    "level_label": alert.get_alert_level_display(),
                    "probability": round(alert.probability, 4),
                    "generated_at": alert.generated_at.isoformat(),
                    "model_version": alert.model_version,
                    "color": self.COLORS.get(alert.alert_level, "#6b7280"),
                },
            })
        return Response({"type": "FeatureCollection", "features": features})
