from django.urls import path

from apps.jobs.views import DispatchJobView, JobDetailView, JobListView

urlpatterns = [
    path("", JobListView.as_view(), name="job-list"),
    path("dispatch/", DispatchJobView.as_view(), name="job-dispatch"),
    path("<str:task_id>/", JobDetailView.as_view(), name="job-detail"),
]
