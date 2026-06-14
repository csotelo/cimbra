"""Widget auto-discovery registry.

Each app declares its widgets in a widgets.py file.
On startup, CoreConfig.ready() calls widget_registry.autodiscover()
which scans all INSTALLED_APPS, imports their widgets.py, and syncs to DB.
"""

import importlib
import logging

from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class WidgetDefinition:
    module_slug: str
    module_label: str
    name: str
    label: str
    description: str
    vue_component: str
    default_visible: bool = False
    is_staff_only: bool = False


class WidgetRegistry:
    """Collects widget definitions from all apps and syncs them to DB."""

    def __init__(self):
        self._definitions: list[WidgetDefinition] = []

    def register(
        self,
        module: str,
        module_label: str,
        name: str,
        label: str,
        vue_component: str,
        description: str = "",
        default_visible: bool = False,
        is_staff_only: bool = False,
    ):
        self._definitions.append(WidgetDefinition(
            module_slug=module,
            module_label=module_label,
            name=name,
            label=label,
            description=description,
            vue_component=vue_component,
            default_visible=default_visible,
            is_staff_only=is_staff_only,
        ))

    def autodiscover(self):
        """Import widgets.py from every installed app, then sync to DB."""
        from django.apps import apps

        for app_config in apps.get_app_configs():
            try:
                importlib.import_module(f"{app_config.name}.widgets")
            except ImportError:
                pass
            except Exception as e:
                logger.warning(f"Error loading widgets from {app_config.name}: {e}")

        self._sync_to_db()

    def _sync_to_db(self):
        """Create or update Module and Widget records. Never deletes user prefs."""
        try:
            from apps.dashboard.models import Module, Widget

            for defn in self._definitions:
                module, _ = Module.objects.update_or_create(
                    slug=defn.module_slug,
                    defaults={"label": defn.module_label},
                )
                Widget.objects.update_or_create(
                    module=module,
                    name=defn.name,
                    defaults={
                        "label": defn.label,
                        "description": defn.description,
                        "vue_component": defn.vue_component,
                        "default_visible": defn.default_visible,
                        "is_staff_only": defn.is_staff_only,
                    },
                )
        except Exception as e:
            # DB may not be ready yet (first migrate). Fail silently.
            logger.debug(f"Widget sync skipped: {e}")


widget_registry = WidgetRegistry()
