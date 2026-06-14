"""URL Configuration."""

from django.apps import apps as django_apps
from django.conf import settings
from django.contrib import admin
from django.http import HttpResponse, JsonResponse
from django.urls import include, path

from config.settings import INSTALLED_APPS

admin.site.site_header = "Ximbra"
admin.site.site_title = "Ximbra Admin"
admin.site.index_title = "Panel de administración"


def robots_txt(request):
    """robots.txt dinámico — lee allow_indexing de SiteConfig."""
    allow = False
    try:
        from core.models import SiteConfig
        allow = SiteConfig.get_solo().allow_indexing
    except Exception:
        allow = getattr(settings, "ALLOW_INDEXING", False)

    if allow:
        content = "User-agent: *\nAllow: /\n"
    else:
        content = "User-agent: *\nDisallow: /\n"
    return HttpResponse(content, content_type="text/plain")


def system_config(request):
    """Endpoint público de configuración del sistema para el frontend."""
    seo = {
        "site_name": "Ximbra",
        "site_description": "",
        "og_image_url": "",
        "favicon_url": "",
        "allow_indexing": False,
        "primary_color": "#4f46e5",
    }
    try:
        from core.models import SiteConfig
        cfg = SiteConfig.get_solo()
        seo.update({
            "site_name": cfg.site_name,
            "site_description": cfg.site_description,
            "og_image_url": cfg.og_image_url,
            "favicon_url": cfg.favicon_url,
            "allow_indexing": cfg.allow_indexing,
            "primary_color": cfg.primary_color,
        })
    except Exception:
        pass

    return JsonResponse({
        "single_tenant_mode": getattr(settings, "SINGLE_TENANT_MODE", True),
        "main_tenant_slug": getattr(settings, "MAIN_TENANT_SLUG", "ximbra"),
        "allow_self_registration": getattr(settings, "ALLOW_SELF_REGISTRATION", True),
        "app_name": seo["site_name"],
        **seo,
    })


urlpatterns = [
    path("robots.txt", robots_txt),
    path("api/config/", system_config),
    path("api/config/site/", include("core.urls")),
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
    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns

for _app_config in django_apps.get_app_configs():
    if getattr(_app_config, "vigilo_module", False):
        _prefix = getattr(_app_config, "api_prefix", _app_config.label)
        urlpatterns += [path(f"api/{_prefix}/", include(f"{_app_config.name}.urls"))]

if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()
