"""URL patterns for plans app."""

from django.urls import path

from apps.plans.views import MyPlanView, MyUsageView

urlpatterns = [
    path("me/", MyPlanView.as_view(), name="my-plan"),
    path("usage/", MyUsageView.as_view(), name="my-usage"),
]
