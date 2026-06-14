"""Core app configuration."""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        from django.db.models.signals import post_migrate

        def on_post_migrate(sender, **kwargs):
            from core.widgets import widget_registry
            widget_registry.autodiscover()

        # Sync on migrate (clean path — no DB-in-ready warning)
        post_migrate.connect(on_post_migrate)

        # Also sync on startup if tables already exist (server restart without migrate)
        try:
            import django.db
            django.db.connection.ensure_connection()
            from core.widgets import widget_registry
            widget_registry.autodiscover()
        except Exception:
            pass
