"""Carga estaciones meteorológicas de referencia en Perú."""
from django.core.management.base import BaseCommand

from apps.weather.models import Station

STATIONS = [
    {"code": "PE-LIM-01", "name": "Lima - Campo de Marte", "department": "Lima", "latitude": -12.0732, "longitude": -77.0481, "altitude_m": 154},
    {"code": "PE-CUS-01", "name": "Cusco", "department": "Cusco", "latitude": -13.5319, "longitude": -71.9675, "altitude_m": 3399},
    {"code": "PE-AQP-01", "name": "Arequipa - La Pampilla", "department": "Arequipa", "latitude": -16.3220, "longitude": -71.5700, "altitude_m": 2491},
    {"code": "PE-IQT-01", "name": "Iquitos", "department": "Loreto", "latitude": -3.7490, "longitude": -73.2530, "altitude_m": 126},
    {"code": "PE-PIU-01", "name": "Piura", "department": "Piura", "latitude": -5.1945, "longitude": -80.6328, "altitude_m": 55},
    {"code": "PE-JUN-01", "name": "Huancayo", "department": "Junín", "latitude": -12.0651, "longitude": -75.2049, "altitude_m": 3271},
    {"code": "PE-PUN-01", "name": "Puno", "department": "Puno", "latitude": -15.8402, "longitude": -70.0219, "altitude_m": 3827},
    {"code": "PE-CAJ-01", "name": "Cajamarca", "department": "Cajamarca", "latitude": -7.1638, "longitude": -78.5006, "altitude_m": 2720},
    {"code": "PE-HUC-01", "name": "Huánuco", "department": "Huánuco", "latitude": -9.9305, "longitude": -76.2401, "altitude_m": 1894},
    {"code": "PE-TUM-01", "name": "Tumbes", "department": "Tumbes", "latitude": -3.5669, "longitude": -80.4515, "altitude_m": 15},
]


class Command(BaseCommand):
    help = "Carga estaciones meteorológicas de referencia en Perú"

    def handle(self, *args, **options):
        created = 0
        for data in STATIONS:
            _, is_new = Station.objects.get_or_create(code=data["code"], defaults=data)
            if is_new:
                created += 1
        self.stdout.write(self.style.SUCCESS(f"{created} estaciones creadas ({len(STATIONS) - created} ya existían)"))
