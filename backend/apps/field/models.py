"""Field operations models: employees, projects, and geo-fences."""

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
