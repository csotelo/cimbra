"""Field operations models: employees, projects, geo-fences, mobile refuges, positions."""

import uuid

from django.contrib.gis.db import models

from apps.tenants.models import Tenant


class Employee(models.Model):
    """Field worker — not necessarily a system user."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="employees")
    full_name = models.CharField(max_length=200)
    document_number = models.CharField(max_length=20)
    device_id = models.CharField(
        max_length=100,
        unique=True,
        help_text="Identificador único del dispositivo móvil — usado para MQTT tracking",
    )
    fcm_token = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Token FCM para notificaciones push de alertas",
    )
    photo = models.CharField(
        max_length=500,
        blank=True,
        default="",
        help_text="Path en MinIO",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "field_employees"
        ordering = ["full_name"]
        indexes = [
            models.Index(fields=["tenant", "is_active"]),
            models.Index(fields=["device_id"]),
        ]

    def __str__(self):
        return f"{self.full_name} ({self.document_number})"


class Project(models.Model):
    """Construction / field work project."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="projects")
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    employees = models.ManyToManyField(
        Employee,
        related_name="projects",
        blank=True,
        help_text="Empleados asignados a esta obra",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "field_projects"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant", "is_active"]),
        ]

    def __str__(self):
        return self.name


class GeoFence(models.Model):
    """Geographic perimeter defining a work front within a project."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="geofences")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="fences")
    name = models.CharField(max_length=200)
    perimeter = models.PolygonField(srid=4326, geography=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "field_geofences"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["tenant", "is_active"]),
            models.Index(fields=["project"]),
        ]

    def __str__(self):
        return f"{self.name} — {self.project.name}"


class MobileRefuge(models.Model):
    """Mobile refuge unit (vehicle). Position = conductor's GPS position via MQTT."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="mobile_refuges")
    code = models.CharField(max_length=50, help_text="Código identificador de la unidad")
    plate = models.CharField(max_length=20, blank=True, default="", help_text="Placa del vehículo")
    capacity = models.PositiveSmallIntegerField(default=10, help_text="Capacidad de personas")
    conductor = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="mobile_refuges",
        help_text="Empleado conductor — su posición MQTT es la posición de esta unidad",
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="mobile_refuges",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "field_mobile_refuges"
        ordering = ["code"]
        indexes = [
            models.Index(fields=["tenant", "is_active"]),
        ]

    def __str__(self):
        return f"{self.code} ({self.plate or 'sin placa'})"


class EmployeePosition(models.Model):
    """Time-series table for GPS positions received via MQTT from field devices."""

    id = models.BigAutoField(primary_key=True)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="positions", db_index=True
    )
    entity_id = models.UUIDField(db_index=True)
    entity_type = models.CharField(max_length=30)  # "employee"
    latitude = models.FloatField()
    longitude = models.FloatField()
    accuracy = models.FloatField(null=True, blank=True)
    recorded_at = models.DateTimeField()
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "field_positions"
        ordering = ["-recorded_at"]
        indexes = [
            models.Index(fields=["tenant", "entity_id", "-recorded_at"]),
        ]

    def __str__(self):
        return f"{self.entity_type}:{self.entity_id} @ {self.recorded_at}"
