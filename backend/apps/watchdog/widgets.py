from core.widgets import widget_registry

widget_registry.register(
    module="watchdog",
    module_label="Watchdog",
    name="service_health",
    label="Estado de Servicios",
    description="Indicador verde/rojo por servicio — heartbeat via Redis Stream.",
    vue_component="ServiceHealth",
    default_visible=True,
    is_staff_only=True,
)
