"""
DTOs para la API de calidad del aire
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator


class PollutantRequestDTO(BaseModel):
    """DTO para solicitudes de datos de contaminantes"""
    
    parameter: str = Field(
        default="no2",
        description="Tipo de contaminante (no2, so2, o3, hcho)",
        example="no2"
    )
    bbox: Optional[str] = Field(
        default=None,
        description="Bounding box como 'minLon,minLat,maxLon,maxLat'",
        example="-58.5,-34.7,-58.3,-34.5"
    )
    lat: Optional[float] = Field(
        default=None,
        description="Latitud del punto",
        ge=-90,
        le=90,
        example=-34.6
    )
    lon: Optional[float] = Field(
        default=None,
        description="Longitud del punto",
        ge=-180,
        le=180,
        example=-58.4
    )
    limit: int = Field(
        default=100,
        description="Límite de resultados",
        ge=1,
        le=500,
        example=100
    )
    start: Optional[datetime] = Field(
        default=None,
        description="Fecha de inicio en formato UTC ISO",
        example="2024-01-01T00:00:00Z"
    )
    end: Optional[datetime] = Field(
        default=None,
        description="Fecha de fin en formato UTC ISO",
        example="2024-01-01T23:59:59Z"
    )
    
    @validator('parameter')
    def validate_parameter(cls, v):
        """Validar tipo de contaminante"""
        valid_params = ['no2', 'so2', 'o3', 'hcho']
        if v.lower() not in valid_params:
            raise ValueError(f'Parámetro debe ser uno de: {valid_params}')
        return v.lower()
    
    @validator('bbox')
    def validate_bbox(cls, v):
        """Validar formato de bounding box"""
        if v is None:
            return v
        
        try:
            parts = [float(x.strip()) for x in v.split(",")]
            if len(parts) != 4:
                raise ValueError("Bounding box debe tener 4 valores")
            
            west, south, east, north = parts
            if west >= east or south >= north:
                raise ValueError("Bounding box inválido")
            
            if not (-180 <= west <= 180) or not (-180 <= east <= 180):
                raise ValueError("Longitudes inválidas")
            
            if not (-90 <= south <= 90) or not (-90 <= north <= 90):
                raise ValueError("Latitudes inválidas")
                
        except Exception as e:
            raise ValueError(f"Formato de bounding box inválido: {e}")
        
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "parameter": "no2",
                "bbox": "-58.5,-34.7,-58.3,-34.5",
                "limit": 100
            }
        }


class MeasurementDTO(BaseModel):
    """DTO para mediciones individuales"""
    
    latitude: float = Field(description="Latitud")
    longitude: float = Field(description="Longitud")
    parameter: str = Field(description="Tipo de contaminante")
    value: float = Field(description="Valor de la medición")
    unit: str = Field(description="Unidad de medida")
    timestamp: str = Field(description="Timestamp de la medición")
    
    class Config:
        schema_extra = {
            "example": {
                "latitude": -34.6,
                "longitude": -58.4,
                "parameter": "no2",
                "value": 15.5,
                "unit": "mol/m^2",
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }


class PollutantResponseDTO(BaseModel):
    """DTO para respuestas de datos de contaminantes"""
    
    source: str = Field(description="Fuente de los datos")
    results: List[List[Any]] = Field(description="Lista de mediciones")
    
    class Config:
        schema_extra = {
            "example": {
                "source": "nasa-tempo",
                "results": [
                    [-34.6, -58.4, "no2", 15.5, "mol/m^2", "2024-01-01T12:00:00Z"]
                ]
            }
        }


class PollutantInfoDTO(BaseModel):
    """DTO para información de contaminantes"""
    
    name: str = Field(description="Nombre del contaminante")
    description: str = Field(description="Descripción del contaminante")
    health_impact: str = Field(description="Impacto en la salud")
    collection_id: str = Field(description="ID de colección TEMPO")
    variable_name: str = Field(description="Nombre de variable")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "no2",
                "description": "Dióxido de nitrógeno - indicador de emisiones del transporte",
                "health_impact": "Agrava enfermedades respiratorias",
                "collection_id": "C2930725014-LARC_CLOUD",
                "variable_name": "nitrogendioxide_tropospheric_column"
            }
        }


class SupportedPollutantsDTO(BaseModel):
    """DTO para contaminantes soportados"""
    
    supported_pollutants: List[str] = Field(description="Lista de contaminantes soportados")
    descriptions: Dict[str, str] = Field(description="Descripciones de contaminantes")
    health_impacts: Dict[str, str] = Field(description="Impactos en salud")
    
    class Config:
        schema_extra = {
            "example": {
                "supported_pollutants": ["no2", "so2", "o3", "hcho"],
                "descriptions": {
                    "no2": "Dióxido de nitrógeno",
                    "so2": "Dióxido de azufre"
                },
                "health_impacts": {
                    "no2": "Agrava enfermedades respiratorias",
                    "so2": "Causa irritación"
                }
            }
        }


class ErrorResponseDTO(BaseModel):
    """DTO para respuestas de error"""
    
    error: str = Field(description="Tipo de error")
    message: str = Field(description="Mensaje de error")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Detalles adicionales")
    
    class Config:
        schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Parámetro inválido",
                "details": {"parameter": "invalid_value"}
            }
        }
