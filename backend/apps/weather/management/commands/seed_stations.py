"""Carga estaciones meteorológicas de referencia en Perú."""
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand

from apps.weather.models import Station

STATIONS = [
    {"code": "PE-LIM-01", "name": "Lima - Campo de Marte",    "department": "Lima",      "lat": -12.0732, "lon": -77.0481, "altitude_m": 154},
    {"code": "PE-CUS-01", "name": "Cusco",                    "department": "Cusco",     "lat": -13.5319, "lon": -71.9675, "altitude_m": 3399},
    {"code": "PE-AQP-01", "name": "Arequipa - La Pampilla",   "department": "Arequipa",  "lat": -16.3220, "lon": -71.5700, "altitude_m": 2491},
    {"code": "PE-IQT-01", "name": "Iquitos",                  "department": "Loreto",    "lat": -3.7490,  "lon": -73.2530, "altitude_m": 126},
    {"code": "PE-PIU-01", "name": "Piura",                    "department": "Piura",     "lat": -5.1945,  "lon": -80.6328, "altitude_m": 55},
    {"code": "PE-JUN-01", "name": "Huancayo",                 "department": "Junín",     "lat": -12.0651, "lon": -75.2049, "altitude_m": 3271},
    {"code": "PE-PUN-01", "name": "Puno",                     "department": "Puno",      "lat": -15.8402, "lon": -70.0219, "altitude_m": 3827},
    {"code": "PE-CAJ-01", "name": "Cajamarca",                "department": "Cajamarca", "lat": -7.1638,  "lon": -78.5006, "altitude_m": 2720},
    {"code": "PE-HUC-01", "name": "Huánuco",                  "department": "Huánuco",   "lat": -9.9305,  "lon": -76.2401, "altitude_m": 1894},
    {"code": "PE-TUM-01", "name": "Tumbes",                   "department": "Tumbes",    "lat": -3.5669,  "lon": -80.4515, "altitude_m": 15},
]


class Command(BaseCommand):
    help = "Carga estaciones meteorológicas de referencia en Perú"

    def handle(self, *args, **options):
        created = 0
        for row in STATIONS:
            defaults = {
                "name": row["name"],
                "department": row["department"],
                "altitude_m": row["altitude_m"],
                "location": Point(row["lon"], row["lat"], srid=4326),
            }
            _, is_new = Station.objects.get_or_create(code=row["code"], defaults=defaults)
            if is_new:
                created += 1
        self.stdout.write(self.style.SUCCESS(
            f"{created} estaciones creadas ({len(STATIONS) - created} ya existían)"
        ))
