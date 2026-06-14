from django.urls import path
from apps.dashboard.views import DashboardWidgetsView

urlpatterns = [
    path("", DashboardWidgetsView.as_view(), name="dashboard-widgets"),
]
