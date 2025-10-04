"""
Modelo de dominio para ubicación geográfica
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class GeoLocation:
    """Representa una ubicación geográfica"""
    
    latitude: float
    longitude: float
    
    def __post_init__(self):
        """Validar coordenadas"""
        if not (-90 <= self.latitude <= 90):
            raise ValueError(f"Latitud inválida: {self.latitude}")
        if not (-180 <= self.longitude <= 180):
            raise ValueError(f"Longitud inválida: {self.longitude}")
    
    @property
    def lat(self) -> float:
        """Alias para latitude"""
        return self.latitude
    
    @property
    def lon(self) -> float:
        """Alias para longitude"""
        return self.longitude
    
    def to_dict(self) -> dict:
        """Convertir a diccionario"""
        return {
            "latitude": self.latitude,
            "longitude": self.longitude
        }


@dataclass
class BoundingBox:
    """Representa un bounding box geográfico"""
    
    west: float
    south: float
    east: float
    north: float
    
    def __post_init__(self):
        """Validar bounding box"""
        if self.west >= self.east:
            raise ValueError("West debe ser menor que East")
        if self.south >= self.north:
            raise ValueError("South debe ser menor que North")
        if not (-180 <= self.west <= 180):
            raise ValueError(f"West inválido: {self.west}")
        if not (-180 <= self.east <= 180):
            raise ValueError(f"East inválido: {self.east}")
        if not (-90 <= self.south <= 90):
            raise ValueError(f"South inválido: {self.south}")
        if not (-90 <= self.north <= 90):
            raise ValueError(f"North inválido: {self.north}")
    
    @classmethod
    def from_point(cls, lat: float, lon: float, delta: float = 0.2) -> "BoundingBox":
        """Crear bounding box desde un punto con delta"""
        return cls(
            west=lon - delta,
            south=lat - delta,
            east=lon + delta,
            north=lat + delta
        )
    
    @classmethod
    def from_string(cls, bbox_str: str) -> "BoundingBox":
        """Crear bounding box desde string 'minLon,minLat,maxLon,maxLat'"""
        try:
            parts = [float(x.strip()) for x in bbox_str.split(",")]
            if len(parts) != 4:
                raise ValueError("Bounding box debe tener 4 valores")
            return cls(west=parts[0], south=parts[1], east=parts[2], north=parts[3])
        except Exception as e:
            raise ValueError(f"Formato de bounding box inválido: {bbox_str}") from e
    
    def to_string(self) -> str:
        """Convertir a string"""
        return f"{self.west},{self.south},{self.east},{self.north}"
    
    def to_dict(self) -> dict:
        """Convertir a diccionario"""
        return {
            "west": self.west,
            "south": self.south,
            "east": self.east,
            "north": self.north
        }
