"""URL routing for field operations."""

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    EmployeeViewSet,
    GeoFenceViewSet,
    MobileRefugeViewSet,
    ProjectViewSet,
    TrackingLiveView,
)

router = DefaultRouter()
router.register("employees", EmployeeViewSet, basename="employee")
router.register("projects", ProjectViewSet, basename="project")
router.register("fences", GeoFenceViewSet, basename="geofence")
router.register("refuges", MobileRefugeViewSet, basename="mobile-refuge")

urlpatterns = router.urls + [
    path("tracking/live/", TrackingLiveView.as_view(), name="tracking-live"),
]
