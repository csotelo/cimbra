"""Plans app configuration."""

from django.apps import AppConfig


class PlansConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.plans"
    verbose_name = "Plans"

    def ready(self):
        import apps.plans.signals  # noqa: F401
