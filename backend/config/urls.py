"""URL Configuration."""

from django.apps import apps as django_apps
from django.conf import settings
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path

from config.settings import INSTALLED_APPS

admin.site.site_header = "Ximbra"
admin.site.site_title = "Ximbra Admin"
admin.site.index_title = "Panel de administración"


def robots_txt(request):
    return HttpResponse("User-agent: *\nDisallow: /\n", content_type="text/plain")


def system_config(request):
    """Public endpoint exposing read-only system configuration for the frontend."""
    from django.http import JsonResponse

    return JsonResponse({
        "single_tenant_mode": getattr(settings, "SINGLE_TENANT_MODE", True),
        "main_tenant_slug": getattr(settings, "MAIN_TENANT_SLUG", "ximbra"),
        "allow_self_registration": getattr(settings, "ALLOW_SELF_REGISTRATION", True),
        "app_name": "Ximbra",
    })


urlpatterns = [
    path("robots.txt", robots_txt),
    path("api/config/", system_config),
    path("admin/", admin.site.urls),
    path("api/users/", include("apps.users.urls")),
    path("api/tenants/", include("apps.tenants.urls")),
    path("api/tokens/", include("apps.api_tokens.urls")),
    path("api/jobs/", include("apps.jobs.urls")),
    path("api/plans/", include("apps.plans.urls")),
    path("api/dashboard/", include("apps.dashboard.urls")),
    path("api/watchdog/", include("apps.watchdog.urls")),
    path("api/notifications/", include("apps.notifications.urls")),
]

if "debug_toolbar" in INSTALLED_APPS:
    import debug_toolbar

    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns

for _app_config in django_apps.get_app_configs():
    if getattr(_app_config, "vigilo_module", False):
        _prefix = getattr(_app_config, "api_prefix", _app_config.label)
        urlpatterns += [path(f"api/{_prefix}/", include(f"{_app_config.name}.urls"))]

if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()
