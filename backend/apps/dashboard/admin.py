from django.contrib import admin
from apps.dashboard.models import Module, UserDashboard, Widget


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ["slug", "label", "is_enabled", "created_at"]
    list_filter = ["is_enabled"]


@admin.register(Widget)
class WidgetAdmin(admin.ModelAdmin):
    list_display = ["name", "module", "label", "vue_component", "default_visible"]
    list_filter = ["module"]
    search_fields = ["name", "label"]


@admin.register(UserDashboard)
class UserDashboardAdmin(admin.ModelAdmin):
    list_display = ["user", "widget", "position", "is_visible"]
    list_filter = ["is_visible"]
    raw_id_fields = ["user"]
