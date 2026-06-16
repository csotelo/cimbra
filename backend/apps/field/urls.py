"""URL routing for field operations."""

from rest_framework.routers import DefaultRouter

from .views import EmployeeViewSet, GeoFenceViewSet, ProjectViewSet

router = DefaultRouter()
router.register("employees", EmployeeViewSet, basename="employee")
router.register("projects", ProjectViewSet, basename="project")
router.register("fences", GeoFenceViewSet, basename="geofence")

urlpatterns = router.urls
