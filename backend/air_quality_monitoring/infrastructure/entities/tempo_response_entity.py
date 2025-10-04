"""
Entidades de infraestructura para respuestas de NASA TEMPO
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class TempoResponseEntity:
    """Entidad para respuestas de NASA TEMPO"""
    
    source: str
    results: List[List[Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return {
            "source": self.source,
            "results": self.results
        }


@dataclass
class GeoJsonFeature:
    """Entidad para features de GeoJSON"""
    
    geometry: Dict[str, Any]
    properties: Dict[str, Any]
    
    def is_point(self) -> bool:
        """Verificar si es un punto"""
        return self.geometry.get("type") == "Point"
    
    def get_coordinates(self) -> Optional[List[float]]:
        """Obtener coordenadas"""
        coords = self.geometry.get("coordinates")
        if isinstance(coords, list) and len(coords) >= 2:
            return coords
        return None
    
    def get_value(self) -> Optional[float]:
        """Obtener valor de la medición"""
        props = self.properties
        for key in ["value", "measurement", "mean", "average"]:
            if key in props and props[key] is not None:
                return float(props[key])
        return None
    
    def get_unit(self) -> str:
        """Obtener unidad"""
        props = self.properties
        for key in ["unit", "units"]:
            if key in props:
                return str(props[key])
        return ""
    
    def get_timestamp(self) -> Optional[str]:
        """Obtener timestamp"""
        props = self.properties
        for key in ["datetime", "time", "timestamp"]:
            if key in props and props[key] is not None:
                return str(props[key])
        return None


@dataclass
class NetCdfDatasetEntity:
    """Entidad para datasets NetCDF"""
    
    variable_name: str
    lat_values: Any
    lon_values: Any
    data_values: Any
    units: str
    timestamp: Optional[str]
    
    def get_shape(self) -> tuple:
        """Obtener forma de los datos"""
        return self.data_values.shape if hasattr(self.data_values, 'shape') else ()
    
    def is_valid(self) -> bool:
        """Verificar si el dataset es válido"""
        return (
            self.variable_name is not None and
            self.lat_values is not None and
            self.lon_values is not None and
            self.data_values is not None
        )
