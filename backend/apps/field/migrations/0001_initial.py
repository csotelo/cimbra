"""Initial migration for field app — Employee, Project, GeoFence."""

import uuid

import django.contrib.gis.db.models.fields
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("tenants", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Employee",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("full_name", models.CharField(max_length=200)),
                ("document_number", models.CharField(max_length=20)),
                ("device_id", models.CharField(
                    help_text="Identificador único del dispositivo móvil — usado para MQTT tracking",
                    max_length=100,
                    unique=True,
                )),
                ("fcm_token", models.CharField(
                    blank=True,
                    default="",
                    help_text="Token FCM para notificaciones push de alertas",
                    max_length=255,
                )),
                ("photo", models.CharField(blank=True, default="", help_text="Path en MinIO", max_length=500)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("tenant", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="employees",
                    to="tenants.tenant",
                )),
            ],
            options={
                "db_table": "field_employees",
                "ordering": ["full_name"],
            },
        ),
        migrations.CreateModel(
            name="Project",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=200)),
                ("description", models.TextField(blank=True, default="")),
                ("start_date", models.DateField()),
                ("end_date", models.DateField(blank=True, null=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("tenant", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="projects",
                    to="tenants.tenant",
                )),
                ("employees", models.ManyToManyField(
                    blank=True,
                    help_text="Empleados asignados a esta obra",
                    related_name="projects",
                    to="field.employee",
                )),
            ],
            options={
                "db_table": "field_projects",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="GeoFence",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=200)),
                ("perimeter", django.contrib.gis.db.models.fields.PolygonField(geography=True, srid=4326)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("tenant", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="geofences",
                    to="tenants.tenant",
                )),
                ("project", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="fences",
                    to="field.project",
                )),
            ],
            options={
                "db_table": "field_geofences",
                "ordering": ["name"],
            },
        ),
        migrations.AddIndex(
            model_name="employee",
            index=models.Index(fields=["tenant", "is_active"], name="field_empl_tenant_active_idx"),
        ),
        migrations.AddIndex(
            model_name="employee",
            index=models.Index(fields=["device_id"], name="field_empl_device_id_idx"),
        ),
        migrations.AddIndex(
            model_name="project",
            index=models.Index(fields=["tenant", "is_active"], name="field_proj_tenant_active_idx"),
        ),
        migrations.AddIndex(
            model_name="geofence",
            index=models.Index(fields=["tenant", "is_active"], name="field_fence_tenant_active_idx"),
        ),
        migrations.AddIndex(
            model_name="geofence",
            index=models.Index(fields=["project"], name="field_fence_project_idx"),
        ),
    ]
