"""Django Admin for field operations."""

from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin

from .models import Employee, GeoFence, MobileRefuge, Project, RefugePoint


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


@admin.register(MobileRefuge)
class MobileRefugeAdmin(admin.ModelAdmin):
    list_display = ["code", "plate", "capacity", "conductor", "project", "tenant", "is_active", "created_at"]
    list_filter = ["is_active", "tenant", "project"]
    search_fields = ["code", "plate", "conductor__full_name"]
    list_editable = ["is_active"]
    readonly_fields = ["id", "created_at"]
    ordering = ["code"]

    fieldsets = (
        (None, {"fields": ("id", "tenant", "code", "plate", "capacity")}),
        ("Asignación", {"fields": ("conductor", "project")}),
        ("Estado", {"fields": ("is_active", "created_at")}),
    )


@admin.register(RefugePoint)
class RefugePointAdmin(GISModelAdmin):
    list_display = ["name", "capacity", "project", "tenant", "is_active", "created_at"]
    list_filter = ["is_active", "tenant", "project"]
    search_fields = ["name", "description"]
    list_editable = ["is_active"]
    readonly_fields = ["id", "created_at"]
    ordering = ["name"]

    fieldsets = (
        (None, {"fields": ("id", "tenant", "name", "description", "location")}),
        ("Capacidad y proyecto", {"fields": ("capacity", "project")}),
        ("Estado", {"fields": ("is_active", "created_at")}),
    )
