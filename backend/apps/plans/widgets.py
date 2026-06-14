"""Widget definitions for the Plans module."""

from core.widgets import widget_registry

widget_registry.register(
    module="plans",
    module_label="Planes y Suscripción",
    name="rate_limit_gauge",
    label="Consumo Rate Limit",
    description="Uso actual vs límite del plan en el minuto activo, con indicador visual.",
    vue_component="RateLimitGauge",
    default_visible=True,
)

widget_registry.register(
    module="plans",
    module_label="Planes y Suscripción",
    name="usage_history",
    label="Historial de Consumo",
    description="Requests consumidos en la hora y el día actual vs cuota del plan.",
    vue_component="UsageHistory",
    default_visible=True,
)
