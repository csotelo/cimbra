from django.apps import AppConfig


class WeatherConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.weather"
    label = "weather"
    verbose_name = "Meteorología"

    vigilo_module = True
    api_prefix = "weather"
