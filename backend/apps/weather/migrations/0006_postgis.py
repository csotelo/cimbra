"""Migración a PostGIS: reemplaza DecimalField lat/lon con PointField geography."""
import django.contrib.gis.db.models.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("weather", "0005_ai_analytics"),
    ]

    operations = [
        # 1. Habilitar extensión PostGIS en la base de datos
        migrations.RunSQL(
            "CREATE EXTENSION IF NOT EXISTS postgis",
            reverse_sql="SELECT 1",
        ),
        # 2. Añadir columna location nullable
        migrations.AddField(
            model_name="station",
            name="location",
            field=django.contrib.gis.db.models.fields.PointField(
                geography=True, srid=4326, null=True
            ),
        ),
        # 3. Poblar location desde lat/lon existentes
        migrations.RunSQL(
            """
            UPDATE weather_stations
            SET location = ST_SetSRID(
                ST_MakePoint(longitude::float8, latitude::float8), 4326
            )::geography
            """,
            reverse_sql="SELECT 1",
        ),
        # 4. Hacer location NOT NULL
        migrations.AlterField(
            model_name="station",
            name="location",
            field=django.contrib.gis.db.models.fields.PointField(
                geography=True, srid=4326
            ),
        ),
        # 5. Eliminar campos obsoletos
        migrations.RemoveField(model_name="station", name="latitude"),
        migrations.RemoveField(model_name="station", name="longitude"),
    ]
