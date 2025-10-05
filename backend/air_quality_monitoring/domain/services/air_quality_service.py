from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone

# -------------------------------------------------------------------
# ⬇️ TUS IMPORTACIONES REALES ⬇️
from core.logging import get_logger # Corregida la ruta a core.logging
from utils.exceptions.exceptions import ValidationError, DataSourceError
from air_quality_monitoring.domain.models.geo_location import BoundingBox
from air_quality_monitoring.domain.models.pollutant_data import PollutantType 
from air_quality_monitoring.infrastructure.repositories.nasa_earthaccess_repository import NasaEarthaccessRepository
# -------------------------------------------------------------------


class AirQualityService:
    def __init__(self, repository: NasaEarthaccessRepository):
        self.repository = repository
        self.logger = get_logger("air_quality_service")

    def get_pollutant_measurements(
        self, parameter: str, bbox: Optional[str] = None,
        lat: Optional[float] = None, lon: Optional[float] = None,
        limit: int = 100,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> Dict[str, Any]:
        try:
            self._validate_parameters(parameter, bbox, lat, lon, limit)
            
            bounding_box = None
            if bbox:
                 try:
                    bounding_box = BoundingBox.from_string(bbox)
                 except ValueError as e:
                     raise ValidationError(f"Bounding Box mal formado: {e}") from e

            now_utc = datetime.now(timezone.utc)
            if end and end.tzinfo is None: end = end.replace(tzinfo=timezone.utc)
            if start and start.tzinfo is None: start = start.replace(tzinfo=timezone.utc)
            
            end = end or now_utc
            start = start or (end - timedelta(days=2))

            response = self.repository.get_pollutant_data(
                parameter=parameter, bbox=bounding_box,
                lat=lat, lon=lon, limit=limit, start=start, end=end
            )
            
            self.logger.info(f"Obtenidas {len(response.results)} mediciones para {parameter} de {response.source}")
            return response.to_dict()

        except Exception as e:
            self.logger.error(f"Error obteniendo mediciones: {e}", exc_info=True)
            if isinstance(e, (ValidationError, DataSourceError)):
                raise
            raise DataSourceError(f"Error interno del servicio: {e}") from e

    def get_supported_pollutants(self) -> Dict[str, Any]:
        """Obtiene información sobre los contaminantes soportados y sus detalles."""
        supported_pollutants = self.repository.pollutant_registry.get_all_pollutants()
        
        info = {
            "supported_pollutants": supported_pollutants,
            "descriptions": {p: PollutantType.get_description(p) for p in supported_pollutants},
            "health_impacts": {p: PollutantType.get_health_impact(p) for p in supported_pollutants},
        }
        return info

    def _validate_parameters(self, parameter: str, bbox: Optional[str],
                             lat: Optional[float], lon: Optional[float], limit: int) -> None:
        if not PollutantType.is_valid(parameter):
            raise ValidationError(f"Tipo de contaminante inválido: {parameter}")
        
        if not (1 <= limit <= 500):
            raise ValidationError(f"Límite debe estar entre 1 y 500, recibido: {limit}")
        
        if not bbox and (lat is None or lon is None):
            raise ValidationError("Debe proporcionar bbox o lat/lon")
        if bbox and (lat is not None or lon is not None):
            raise ValidationError("Proporcione bbox O lat/lon, no ambos")
        if lat is not None and not (-90 <= lat <= 90):
            raise ValidationError(f"Latitud inválida: {lat}")
        if lon is not None and not (-180 <= lon <= 180):
            raise ValidationError(f"Longitud inválida: {lon}")