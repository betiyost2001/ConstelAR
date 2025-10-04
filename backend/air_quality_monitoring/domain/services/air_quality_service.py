"""
Servicio de dominio para calidad del aire
"""
from typing import Optional, Dict, Any
from core.logging import get_logger
from utils.exceptions.exceptions import ValidationError, DataSourceError
from air_quality_monitoring.domain.models.geo_location import BoundingBox
from air_quality_monitoring.domain.models.pollutant_data import PollutantType
from air_quality_monitoring.infrastructure.repositories.nasa_harmony_repository import NasaHarmonyRepository


class AirQualityService:
    """Servicio de dominio para calidad del aire"""
    
    def __init__(self, repository: NasaHarmonyRepository):
        """
        Inicializar servicio
        
        Args:
            repository: Repositorio de datos de calidad del aire
        """
        self.repository = repository
        self.logger = get_logger("air_quality_service")
    
    def get_pollutant_measurements(self, parameter: str, bbox: Optional[str] = None,
                                  lat: Optional[float] = None, lon: Optional[float] = None,
                                  limit: int = 100, start: Optional[str] = None,
                                  end: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtener mediciones de contaminantes
        
        Args:
            parameter: Tipo de contaminante (no2, so2, o3, hcho)
            bbox: Bounding box como string "minLon,minLat,maxLon,maxLat"
            lat: Latitud del punto
            lon: Longitud del punto
            limit: Límite de resultados (1-500)
            start: Fecha de inicio en formato ISO
            end: Fecha de fin en formato ISO
        
        Returns:
            Diccionario con datos de mediciones
        
        Raises:
            ValidationError: Error de validación de parámetros
            DataSourceError: Error en la fuente de datos
        """
        try:
            # Validar parámetros
            self._validate_parameters(parameter, bbox, lat, lon, limit)
            
            # Parsear bounding box si se proporciona
            bounding_box = None
            if bbox:
                bounding_box = BoundingBox.from_string(bbox)
            
            # Obtener datos del repositorio
            response = self.repository.get_pollutant_data(
                parameter=parameter,
                bbox=bounding_box,
                lat=lat,
                lon=lon,
                limit=limit,
                start=start,
                end=end
            )
            
            self.logger.info(f"Obtenidas {len(response.results)} mediciones para {parameter}")
            
            return response.to_dict()
            
        except Exception as e:
            self.logger.error(f"Error obteniendo mediciones: {e}")
            if isinstance(e, (ValidationError, DataSourceError)):
                raise
            raise DataSourceError(f"Error interno del servicio: {e}") from e
    
    def get_supported_pollutants(self) -> Dict[str, Any]:
        """
        Obtener lista de contaminantes soportados
        
        Returns:
            Diccionario con información de contaminantes soportados
        """
        pollutants = self.repository.pollutant_registry.get_all_pollutants()
        
        result = {
            "supported_pollutants": pollutants,
            "descriptions": {},
            "health_impacts": {}
        }
        
        for pollutant in pollutants:
            result["descriptions"][pollutant] = PollutantType.get_description(pollutant)
            result["health_impacts"][pollutant] = PollutantType.get_health_impact(pollutant)
        
        return result
    
    def validate_pollutant_type(self, parameter: str) -> bool:
        """
        Validar si un tipo de contaminante es soportado
        
        Args:
            parameter: Tipo de contaminante a validar
        
        Returns:
            True si es soportado
        """
        return PollutantType.is_valid(parameter)
    
    def _validate_parameters(self, parameter: str, bbox: Optional[str], 
                           lat: Optional[float], lon: Optional[float], limit: int) -> None:
        """
        Validar parámetros de entrada
        
        Args:
            parameter: Tipo de contaminante
            bbox: Bounding box
            lat: Latitud
            lon: Longitud
            limit: Límite de resultados
        
        Raises:
            ValidationError: Si algún parámetro es inválido
        """
        # Validar tipo de contaminante
        if not self.validate_pollutant_type(parameter):
            raise ValidationError(f"Tipo de contaminante inválido: {parameter}")
        
        # Validar límite
        if not (1 <= limit <= 500):
            raise ValidationError(f"Límite debe estar entre 1 y 500, recibido: {limit}")
        
        # Validar área geográfica
        if not bbox and (lat is None or lon is None):
            raise ValidationError("Debe proporcionar bbox o lat/lon")
        
        if bbox and (lat is not None or lon is not None):
            raise ValidationError("Proporcione bbox O lat/lon, no ambos")
        
        # Validar coordenadas si se proporcionan
        if lat is not None and lon is not None:
            if not (-90 <= lat <= 90):
                raise ValidationError(f"Latitud inválida: {lat}")
            if not (-180 <= lon <= 180):
                raise ValidationError(f"Longitud inválida: {lon}")
    
    def get_pollutant_info(self, parameter: str) -> Dict[str, Any]:
        """
        Obtener información detallada de un contaminante
        
        Args:
            parameter: Tipo de contaminante
        
        Returns:
            Diccionario con información del contaminante
        
        Raises:
            ValidationError: Si el contaminante no es válido
        """
        if not self.validate_pollutant_type(parameter):
            raise ValidationError(f"Contaminante no soportado: {parameter}")
        
        config = self.repository.pollutant_registry.get_config(parameter)
        
        return {
            "name": config.name,
            "description": config.description,
            "health_impact": config.health_impact,
            "collection_id": config.collection_id,
            "variable_name": config.variable_name
        }
