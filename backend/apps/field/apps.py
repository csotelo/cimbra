from django.apps import AppConfig


class FieldConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.field"
    label = "field"
    verbose_name = "Campo"

    vigilo_module = True
    api_prefix = "field"
