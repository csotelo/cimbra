from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from .models import Station, StormAlert, WeatherObservation
from .serializers import StationSerializer, StormAlertSerializer, WeatherObservationSerializer


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
