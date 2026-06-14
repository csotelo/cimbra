from django.urls import path
from apps.notifications.views import (
    NotificationClearReadView,
    NotificationDetailView,
    NotificationListView,
    NotificationMarkReadView,
    NotificationUnreadCountView,
)

urlpatterns = [
    path("", NotificationListView.as_view(), name="notifications-list"),
    path("unread/", NotificationUnreadCountView.as_view(), name="notifications-unread"),
    path("read-all/", NotificationMarkReadView.as_view(), name="notifications-read-all"),
    path("clear-read/", NotificationClearReadView.as_view(), name="notifications-clear-read"),
    path("<uuid:pk>/read/", NotificationDetailView.as_view(), name="notifications-read"),
]
