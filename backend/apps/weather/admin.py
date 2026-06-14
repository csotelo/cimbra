from django.contrib import admin
from django.utils.html import format_html

from .models import ModelArtifact, Station, StormAlert, TelegramSubscription, WeatherObservation


@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "department", "coords", "altitude_m", "is_active"]
    list_filter = ["department", "is_active"]
    search_fields = ["code", "name", "department"]
    list_editable = ["is_active"]
    ordering = ["department", "name"]

    @admin.display(description="Coordenadas (lat, lon)")
    def coords(self, obj):
        if obj.location:
            return f"{obj.location.y:.4f}, {obj.location.x:.4f}"
        return "—"


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


@admin.register(ModelArtifact)
class ModelArtifactAdmin(admin.ModelAdmin):
    list_display = ["version", "status_badge", "accuracy_pct", "recall_pct", "samples_train", "epochs_run", "training_seconds", "is_active", "created_at"]
    list_filter = ["status", "is_active"]
    readonly_fields = ["id", "created_at", "version", "model_path", "scaler_path",
                       "samples_train", "samples_val", "samples_test",
                       "accuracy", "precision", "recall", "loss",
                       "epochs_run", "training_seconds"]
    ordering = ["-created_at"]

    STATUS_COLORS = {"training": "#6366f1", "ready": "#22c55e", "failed": "#ef4444"}

    @admin.display(description="Estado")
    def status_badge(self, obj):
        color = self.STATUS_COLORS.get(obj.status, "#6b7280")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:4px;font-weight:600">{}</span>',
            color, obj.get_status_display(),
        )

    @admin.display(description="Accuracy")
    def accuracy_pct(self, obj):
        return f"{obj.accuracy:.1%}" if obj.accuracy is not None else "—"

    @admin.display(description="Recall")
    def recall_pct(self, obj):
        return f"{obj.recall:.1%}" if obj.recall is not None else "—"

    def has_add_permission(self, request):
        return False


@admin.register(TelegramSubscription)
class TelegramSubscriptionAdmin(admin.ModelAdmin):
    list_display = ["chat_id", "username", "department_display", "min_level", "is_active", "created_at"]
    list_filter = ["is_active", "min_level"]
    search_fields = ["username", "department"]
    list_editable = ["is_active", "min_level"]
    ordering = ["-created_at"]

    @admin.display(description="Departamento")
    def department_display(self, obj):
        return obj.department or "— todos —"
