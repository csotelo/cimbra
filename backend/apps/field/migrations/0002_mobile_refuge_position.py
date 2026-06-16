"""Migration 0002 — MobileRefuge and EmployeePosition models."""

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("field", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="MobileRefuge",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("code", models.CharField(help_text="Código identificador de la unidad", max_length=50)),
                ("plate", models.CharField(blank=True, default="", help_text="Placa del vehículo", max_length=20)),
                ("capacity", models.PositiveSmallIntegerField(default=10, help_text="Capacidad de personas")),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "conductor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="mobile_refuges",
                        to="field.employee",
                        help_text="Empleado conductor — su posición MQTT es la posición de esta unidad",
                    ),
                ),
                (
                    "project",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="mobile_refuges",
                        to="field.project",
                    ),
                ),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="mobile_refuges",
                        to="tenants.tenant",
                    ),
                ),
            ],
            options={
                "db_table": "field_mobile_refuges",
                "ordering": ["code"],
            },
        ),
        migrations.AddIndex(
            model_name="mobilerefuge",
            index=models.Index(fields=["tenant", "is_active"], name="field_mobil_tenant_active_idx"),
        ),
        migrations.CreateModel(
            name="EmployeePosition",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                (
                    "tenant",
                    models.ForeignKey(
                        db_index=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="positions",
                        to="tenants.tenant",
                    ),
                ),
                ("entity_id", models.UUIDField(db_index=True)),
                ("entity_type", models.CharField(max_length=30)),
                ("latitude", models.FloatField()),
                ("longitude", models.FloatField()),
                ("accuracy", models.FloatField(blank=True, null=True)),
                ("recorded_at", models.DateTimeField()),
                ("received_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "field_positions",
                "ordering": ["-recorded_at"],
            },
        ),
        migrations.AddIndex(
            model_name="employeeposition",
            index=models.Index(fields=["tenant", "entity_id", "-recorded_at"], name="field_pos_tenant_entity_ts_idx"),
        ),
    ]
