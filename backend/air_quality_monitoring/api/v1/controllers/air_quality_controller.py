import asyncio
from datetime import datetime, timezone, timedelta
from typing import Annotated, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

# -------------------------------------------------------------------
# ⬇️ TUS IMPORTACIONES REALES ⬇️
from core.logging import get_logger # Corregida la ruta a core.logging
from air_quality_monitoring.domain.services.air_quality_service import AirQualityService
from utils.exceptions.exceptions import (
    ValidationError,
    DataSourceError,
    DataProcessingError,
)
from air_quality_monitoring.api.v1.dtos.pollutant_request_dto import (
    PollutantResponseDTO,
    PollutantInfoDTO,
    SupportedPollutantsDTO,
)
# Dependencias necesarias para el servicio
from air_quality_monitoring.infrastructure.external_apis.earthaccess_client import EarthaccessClient
from air_quality_monitoring.infrastructure.repositories.nasa_earthaccess_repository import NasaEarthaccessRepository
from core.config.config import get_settings
# -------------------------------------------------------------------

def get_air_quality_service() -> AirQualityService: 
    """Dependencia: Crea el cliente, repositorio y servicio con las configuraciones."""
    settings = get_settings()
    client = EarthaccessClient(settings=settings)
    repo = NasaEarthaccessRepository(client=client)
    return AirQualityService(repository=repo)


logger = get_logger("air_quality_controller")
router = APIRouter()

@router.get(
    "/normalized",
    response_model=PollutantResponseDTO, 
    summary="Obtener mediciones de contaminantes normalizadas",
    description="Obtiene mediciones de contaminantes atmosféricos desde la misión NASA TEMPO (Nivel 2).",
    responses={
        200: {"description": "Mediciones obtenidas exitosamente"},
        400: {"description": "Parámetros inválidos"},
        500: {"description": "Error interno del servidor o de procesamiento"},
        502: {"description": "Error al conectar o acceder a los datos de la NASA/Earthaccess."},
    },
)
async def get_normalized_measurements(
    parameter: str = Query(default="no2", description="Tipo de contaminante (no2, so2, o3, hcho)", example="no2"),
    bbox: Optional[str] = Query(default=None, description="Bounding box como 'minLon,minLat,maxLon,maxLat'", example="-58.5,-34.7,-58.3,-34.5"),
    lat: Optional[float] = Query(default=None, description="Latitud del punto", ge=-90, le=90, example=-34.6),
    lon: Optional[float] = Query(default=None, description="Longitud del punto", ge=-180, le=180, example=-58.4),
    limit: int = Query(default=100, description="Límite de resultados", ge=1, le=500, example=100),
    start: Optional[datetime] = Query(default=None, description="Fecha de inicio en formato UTC ISO (p.ej. 2025-10-01T00:00:00Z)"),
    end: Optional[datetime] = Query(default=None, description="Fecha de fin en formato UTC ISO (p.ej. 2025-10-04T23:59:59Z)"),
    service: Annotated[AirQualityService, Depends(get_air_quality_service)] = None,
) -> Dict[str, Any]:
    try:
        p = (parameter or "").lower()
        ALIASES = {"pm2_5": "no2", "pm25": "no2", "ozone": "o3", "formaldehyde": "hcho", "sulfur_dioxide": "so2"}
        p = ALIASES.get(p, p)

        start_utc = start.replace(tzinfo=timezone.utc) if start and start.tzinfo is None else start
        end_utc = end.replace(tzinfo=timezone.utc) if end and end.tzinfo is None else end
        
        response = await asyncio.to_thread(
            service.get_pollutant_measurements,
            parameter=p,
            bbox=bbox, 
            lat=lat,
            lon=lon,
            limit=limit,
            start=start_utc, 
            end=end_utc, 	 
        )
        return response

    except ValidationError as e:
        logger.warning(f"Error de validación (400): {e}")
        raise HTTPException(status_code=400, detail=f"Parámetros inválidos: {e.message}", headers={"X-Error-Type": "ValidationError"})
    except (DataSourceError, DataProcessingError) as e:
        logger.error(f"Error de fuente de datos o procesamiento (502): {e}", exc_info=True)
        raise HTTPException(status_code=502, detail=f"Error al acceder/procesar datos TEMPO de la NASA: {e.message}", headers={"X-Error-Type": e.__class__.__name__})
    except Exception as e:
        logger.error("Error inesperado en el controlador (500)", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor.", headers={"X-Error-Type": "InternalError"})


@router.get(
    "/pollutants",
    response_model=SupportedPollutantsDTO,
    summary="Obtener lista y detalles de contaminantes soportados"
)
async def get_supported_pollutants(
    service: Annotated[AirQualityService, Depends(get_air_quality_service)] = None,
) -> Dict[str, Any]:
    try:
        info = await asyncio.to_thread(service.get_supported_pollutants)
        return info
    except Exception as e:
        logger.error("Error al obtener contaminantes soportados", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error al obtener la lista de contaminantes: {e}")