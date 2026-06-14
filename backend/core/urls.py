from django.urls import path
from core.views import SiteConfigView

urlpatterns = [
    path("", SiteConfigView.as_view(), name="site_config"),
]
