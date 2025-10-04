"""
Modelo de dominio para mediciones de calidad del aire
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from .geo_location import GeoLocation


@dataclass
class Measurement:
    """Representa una medición de calidad del aire"""
    
    location: GeoLocation
    parameter: str
    value: float
    unit: str
    timestamp: datetime
    source: str = "nasa-tempo"
    
    def __post_init__(self):
        """Validar medición"""
        if not self.parameter:
            raise ValueError("Parámetro es requerido")
        if self.value is None:
            raise ValueError("Valor es requerido")
        if not self.unit:
            raise ValueError("Unidad es requerida")
        if not self.timestamp:
            raise ValueError("Timestamp es requerido")
    
    @property
    def latitude(self) -> float:
        """Latitud de la medición"""
        return self.location.latitude
    
    @property
    def longitude(self) -> float:
        """Longitud de la medición"""
        return self.location.longitude
    
    def to_list(self) -> list:
        """Convertir a lista [lat, lon, parameter, value, unit, datetime]"""
        return [
            self.latitude,
            self.longitude,
            self.parameter,
            self.value,
            self.unit,
            self.timestamp.isoformat()
        ]
    
    def to_dict(self) -> dict:
        """Convertir a diccionario"""
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "parameter": self.parameter,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source
        }


@dataclass
class PollutantData:
    """Representa datos de contaminantes"""
    
    measurements: list[Measurement]
    parameter: str
    total_count: int
    
    def __post_init__(self):
        """Validar datos de contaminantes"""
        if not self.parameter:
            raise ValueError("Parámetro es requerido")
        if self.total_count < 0:
            raise ValueError("Total count debe ser >= 0")
    
    def to_response_dict(self) -> dict:
        """Convertir a formato de respuesta API"""
        return {
            "source": "nasa-tempo",
            "results": [measurement.to_list() for measurement in self.measurements]
        }
    
    def get_latest_measurement(self) -> Optional[Measurement]:
        """Obtener la medición más reciente"""
        if not self.measurements:
            return None
        return max(self.measurements, key=lambda m: m.timestamp)
    
    def get_average_value(self) -> Optional[float]:
        """Obtener valor promedio de las mediciones"""
        if not self.measurements:
            return None
        values = [m.value for m in self.measurements if m.value is not None]
        return sum(values) / len(values) if values else None
