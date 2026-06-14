from django.contrib import admin
from django.utils.html import format_html

from .models import Station, StormAlert, WeatherObservation


@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "department", "latitude", "longitude", "altitude_m", "is_active"]
    list_filter = ["department", "is_active"]
    search_fields = ["code", "name", "department"]
    list_editable = ["is_active"]
    ordering = ["department", "name"]


@admin.register(WeatherObservation)
class WeatherObservationAdmin(admin.ModelAdmin):
    list_display = ["station", "observed_at", "temperature", "humidity", "pressure", "cape", "k_index", "source"]
    list_filter = ["station", "source"]
    search_fields = ["station__code", "station__name"]
    readonly_fields = ["ingested_at", "raw_data"]
    ordering = ["-observed_at"]
    date_hierarchy = "observed_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(StormAlert)
class StormAlertAdmin(admin.ModelAdmin):
    list_display = ["station", "level_badge", "probability_pct", "generated_at", "is_active", "model_version"]
    list_filter = ["alert_level", "is_active", "station"]
    readonly_fields = ["created_at"]
    ordering = ["-generated_at"]
    date_hierarchy = "generated_at"

    COLORS = {1: "#22c55e", 2: "#eab308", 3: "#f97316", 4: "#ef4444"}
    LABELS = {1: "Verde", 2: "Amarillo", 3: "Naranja", 4: "Rojo"}

    @admin.display(description="Nivel")
    def level_badge(self, obj):
        color = self.COLORS.get(obj.alert_level, "#6b7280")
        label = self.LABELS.get(obj.alert_level, str(obj.alert_level))
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:4px;font-weight:600">{}</span>',
            color, label,
        )

    @admin.display(description="Probabilidad")
    def probability_pct(self, obj):
        return f"{obj.probability:.1%}"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
