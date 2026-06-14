from django.urls import path

from .views import (
    AlertGeoView,
    AlertListView,
    ObservationListView,
    StationGeoView,
    StationListView,
    TelegramSubscriptionListView,
)

urlpatterns = [
    path("stations/", StationListView.as_view()),
    path("stations/geojson/", StationGeoView.as_view()),
    path("observations/", ObservationListView.as_view()),
    path("alerts/", AlertListView.as_view()),
    path("alerts/geojson/", AlertGeoView.as_view()),
    path("telegram/subscriptions/", TelegramSubscriptionListView.as_view()),
]
