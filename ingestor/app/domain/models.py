from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Station:
    id: int
    code: str
    name: str
    department: str
    latitude: float
    longitude: float
    altitude_m: Optional[int] = None


@dataclass
class WeatherObservation:
    station_id: int
    observed_at: datetime
    temperature: Optional[float]
    humidity: Optional[float]
    pressure: Optional[float]
    cape: Optional[float]
    k_index: Optional[float]
    source: str = "open-meteo"
    raw_data: dict = field(default_factory=dict)
