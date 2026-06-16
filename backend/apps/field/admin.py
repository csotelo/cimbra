"""Django Admin for field operations."""

from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin

from .models import Employee, GeoFence, Project


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ["full_name", "document_number", "device_id", "tenant", "is_active", "created_at"]
    list_filter = ["is_active", "tenant"]
    search_fields = ["full_name", "document_number", "device_id"]
    list_editable = ["is_active"]
    readonly_fields = ["id", "created_at"]
    ordering = ["full_name"]

    fieldsets = (
        (None, {"fields": ("id", "tenant", "full_name", "document_number")}),
        ("Dispositivo", {"fields": ("device_id", "fcm_token")}),
        ("Foto", {"fields": ("photo",)}),
        ("Estado", {"fields": ("is_active", "created_at")}),
    )


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["name", "tenant", "start_date", "end_date", "employee_count", "is_active", "created_at"]
    list_filter = ["is_active", "tenant"]
    search_fields = ["name", "description"]
    list_editable = ["is_active"]
    readonly_fields = ["id", "created_at"]
    filter_horizontal = ["employees"]
    ordering = ["-created_at"]

    @admin.display(description="Empleados")
    def employee_count(self, obj):
        return obj.employees.count()


@admin.register(GeoFence)
class GeoFenceAdmin(GISModelAdmin):
    list_display = ["name", "project", "tenant", "is_active", "created_at"]
    list_filter = ["is_active", "tenant", "project"]
    search_fields = ["name", "project__name"]
    list_editable = ["is_active"]
    readonly_fields = ["id", "created_at"]
    ordering = ["name"]
