"""Migration 0003 — RefugePoint model."""

import uuid

import django.contrib.gis.db.models.fields
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("field", "0002_mobile_refuge_position"),
    ]

    operations = [
        migrations.CreateModel(
            name="RefugePoint",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=200)),
                ("description", models.TextField(blank=True, default="")),
                (
                    "location",
                    django.contrib.gis.db.models.fields.PointField(
                        geography=True,
                        help_text="Ubicación geográfica del refugio",
                        srid=4326,
                    ),
                ),
                ("capacity", models.PositiveSmallIntegerField(default=50, help_text="Capacidad máxima de personas")),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "project",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="refuge_points",
                        to="field.project",
                    ),
                ),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="refuge_points",
                        to="tenants.tenant",
                    ),
                ),
            ],
            options={
                "db_table": "field_refuge_points",
                "ordering": ["name"],
            },
        ),
        migrations.AddIndex(
            model_name="refugepoint",
            index=models.Index(fields=["tenant", "is_active"], name="field_refuge_tenant_active_idx"),
        ),
    ]
