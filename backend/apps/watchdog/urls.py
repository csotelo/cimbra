from django.urls import path
from apps.watchdog.views import (
    DispatchInternalTaskView,
    SchedulableTasksView,
    ScheduleDetailView,
    ScheduleListView,
    ServiceHealthView,
    WatchdogCommandView,
    WatchdogResultView,
)

urlpatterns = [
    path("health/", ServiceHealthView.as_view(), name="watchdog-health"),
    path("internal/dispatch/", DispatchInternalTaskView.as_view(), name="watchdog-internal-dispatch"),
    path("command/", WatchdogCommandView.as_view(), name="watchdog-command"),
    path("command/<str:command_id>/", WatchdogResultView.as_view(), name="watchdog-result"),
    path("schedules/", ScheduleListView.as_view(), name="watchdog-schedules"),
    path("schedules/tasks/", SchedulableTasksView.as_view(), name="watchdog-schedulable-tasks"),
    path("schedules/<int:pk>/", ScheduleDetailView.as_view(), name="watchdog-schedule-detail"),
]
