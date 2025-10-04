"""
Controlador para la API de calidad del aire
"""
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Annotated, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from core.logging import get_logger
from core.security.dependencies import get_air_quality_service
from utils.exceptions.exceptions import (
    ValidationError,
    DataSourceError,
    DataProcessingError,
)
from air_quality_monitoring.domain.services.air_quality_service import AirQualityService
from air_quality_monitoring.api.v1.dtos.pollutant_request_dto import (
    PollutantResponseDTO,
    PollutantInfoDTO,
    SupportedPollutantsDTO,
)

router = APIRouter()
logger = get_logger("air_quality_controller")


@router.get(
    "/normalized",
    response_model=PollutantResponseDTO,
    summary="Obtener mediciones de contaminantes normalizadas",
    description="""
    Obtiene mediciones de contaminantes atmosféricos desde la misión NASA TEMPO.

    **Características:**
    - Soporta múltiples contaminantes: NO₂, SO₂, O₃, HCHO
    - Datos en tiempo casi real
    - Formato normalizado para fácil integración
    - Muestreo inteligente para optimizar rendimiento

    **Parámetros:**
    - `parameter`: Tipo de contaminante (no2, so2, o3, hcho)
    - `bbox`: Área geográfica como "minLon,minLat,maxLon,maxLat"
    - `lat/lon`: Coordenadas específicas (alternativa a bbox)
    - `limit`: Límite de resultados (1-500)
    - `start/end`: Rango temporal en formato UTC ISO
    """,
    responses={
        200: {"description": "Mediciones obtenidas exitosamente"},
        400: {"description": "Parámetros inválidos"},
        401: {"description": "Error de autenticación NASA"},
        502: {"description": "Error de conexión con NASA Harmony"},
    },
)
async def get_normalized_measurements(
    parameter: str = Query(
        default="no2",
        description="Tipo de contaminante (no2, so2, o3, hcho)",
        example="no2",
    ),
    bbox: Optional[str] = Query(
        default=None,
        description="Bounding box como 'minLon,minLat,maxLon,maxLat'",
        example="-58.5,-34.7,-58.3,-34.5",
    ),
    lat: Optional[float] = Query(
        default=None, description="Latitud del punto", ge=-90, le=90, example=-34.6
    ),
    lon: Optional[float] = Query(
        default=None, description="Longitud del punto", ge=-180, le=180, example=-58.4
    ),
    limit: int = Query(
        default=100, description="Límite de resultados", ge=1, le=500, example=100
    ),
    # ⬇️ Tipados como datetime para parseo automático
    start: Optional[datetime] = Query(
        default=None,
        description="Fecha de inicio en formato UTC ISO (p.ej. 2025-10-01T00:00:00Z)",
        example="2025-10-01T00:00:00Z",
    ),
    end: Optional[datetime] = Query(
        default=None,
        description="Fecha de fin en formato UTC ISO (p.ej. 2025-10-04T23:59:59Z)",
        example="2025-10-04T23:59:59Z",
    ),
    service: Annotated[AirQualityService, Depends(get_air_quality_service)] = None,
) -> Dict[str, Any]:
    try:
        # Normalizar parámetro + alias
        p = (parameter or "").lower()
        ALIASES = {
            "pm2_5": "no2",
            "pm25": "no2",
            "ozone": "o3",
            "formaldehyde": "hcho",
            "sulfur_dioxide": "so2",
        }
        p = ALIASES.get(p, p)
        allowed = {"no2", "so2", "o3", "hcho"}
        if p not in allowed:
            raise ValidationError(f"Tipo de contaminante inválido: {parameter}")

        # Normalizar fechas a UTC y defaults (últimas 48h)
        now = datetime.now(timezone.utc)
        if end is None:
            end = now
        if start is None:
            start = end - timedelta(days=2)

        # Si vinieron naive (sin tz), forzar UTC
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        if start > end:
            start, end = end, start

        logger.info(f"Solicitando mediciones para {p} con límite {limit}")

        # Tolerar service sync o async
        call = service.get_pollutant_measurements(
            parameter=p,
            bbox=bbox,
            lat=lat,
            lon=lon,
            limit=limit,
            start=start,
            end=end,
        )
        result = await call if asyncio.iscoroutine(call) else call

        logger.info(f"Retornando {len(result.get('results', []))} mediciones")
        return result

    except ValidationError as e:
        logger.warning(f"Error de validación: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except DataSourceError as e:
        logger.error(f"Error de fuente de datos: {e}")
        raise HTTPException(status_code=502, detail=str(e))
    except DataProcessingError as e:
        logger.error(f"Error de procesamiento: {e}")
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"Error interno: {e}", exc_info=True)
        raise HTTPException(status_code=502, detail=f"Error interno: {e}")


@router.get(
    "/pollutants/supported",
    response_model=SupportedPollutantsDTO,
    summary="Obtener contaminantes soportados",
)
async def get_supported_pollutants(
    service: Annotated[AirQualityService, Depends(get_air_quality_service)] = None
) -> Dict[str, Any]:
    try:
        return service.get_supported_pollutants()
    except Exception as e:
        logger.error(f"Error obteniendo contaminantes soportados: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get(
    "/pollutants/{parameter}/info",
    response_model=PollutantInfoDTO,
    summary="Obtener información de un contaminante",
)
async def get_pollutant_info(
    parameter: str,
    service: Annotated[AirQualityService, Depends(get_air_quality_service)] = None
) -> Dict[str, Any]:
    try:
        return service.get_pollutant_info(parameter)
    except ValidationError as e:
        logger.warning(f"Contaminante no soportado: {parameter}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error obteniendo información del contaminante: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get(
    "/health",
    summary="Health check del servicio",
)
async def health_check(
    service: Annotated[AirQualityService, Depends(get_air_quality_service)] = None
) -> Dict[str, str]:
    return {"status": "ok", "service": "air_quality_monitoring"}
