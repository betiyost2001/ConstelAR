"""
Controlador para la API de calidad del aire
"""
from typing import Annotated, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from backend.core.logging import get_logger
from backend.core.security.dependencies import get_air_quality_service
from backend.utils.exceptions.exceptions import ValidationError, DataSourceError, DataProcessingError
from backend.air_quality_monitoring.domain.services.air_quality_service import AirQualityService
from backend.air_quality_monitoring.api.v1.dtos.pollutant_request_dto import (
    PollutantRequestDTO, PollutantResponseDTO, PollutantInfoDTO, 
    SupportedPollutantsDTO, ErrorResponseDTO
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
        200: {
            "description": "Mediciones obtenidas exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "source": "nasa-tempo",
                        "results": [
                            [-34.6, -58.4, "no2", 15.5, "mol/m^2", "2024-01-01T12:00:00Z"]
                        ]
                    }
                }
            }
        },
        400: {"description": "Parámetros inválidos"},
        401: {"description": "Error de autenticación NASA"},
        502: {"description": "Error de conexión con NASA Harmony"}
    }
)
async def get_normalized_measurements(
    parameter: str = Query(
        default="no2",
        description="Tipo de contaminante (no2, so2, o3, hcho)",
        example="no2"
    ),
    bbox: str = Query(
        default=None,
        description="Bounding box como 'minLon,minLat,maxLon,maxLat'",
        example="-58.5,-34.7,-58.3,-34.5"
    ),
    lat: float = Query(
        default=None,
        description="Latitud del punto",
        ge=-90,
        le=90,
        example=-34.6
    ),
    lon: float = Query(
        default=None,
        description="Longitud del punto",
        ge=-180,
        le=180,
        example=-58.4
    ),
    limit: int = Query(
        default=100,
        description="Límite de resultados",
        ge=1,
        le=500,
        example=100
    ),
    start: str = Query(
        default=None,
        description="Fecha de inicio en formato UTC ISO",
        example="2024-01-01T00:00:00Z"
    ),
    end: str = Query(
        default=None,
        description="Fecha de fin en formato UTC ISO",
        example="2024-01-01T23:59:59Z"
    ),
    service: Annotated[AirQualityService, Depends(get_air_quality_service)] = None
) -> Dict[str, Any]:
    """
    Obtener mediciones de contaminantes normalizadas
    
    Este endpoint proporciona acceso a datos de calidad del aire desde la misión
    NASA TEMPO, con soporte para múltiples contaminantes y formatos de datos.
    """
    try:
        logger.info(f"Solicitando mediciones para {parameter} con límite {limit}")
        
        result = service.get_pollutant_measurements(
            parameter=parameter,
            bbox=bbox,
            lat=lat,
            lon=lon,
            limit=limit,
            start=start,
            end=end
        )
        
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
        logger.error(f"Error interno: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get(
    "/pollutants/supported",
    response_model=SupportedPollutantsDTO,
    summary="Obtener contaminantes soportados",
    description="Obtiene la lista de contaminantes soportados con sus descripciones e impactos en salud.",
    responses={
        200: {
            "description": "Lista de contaminantes soportados",
            "content": {
                "application/json": {
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
            }
        }
    }
)
async def get_supported_pollutants(
    service: Annotated[AirQualityService, Depends(get_air_quality_service)] = None
) -> Dict[str, Any]:
    """Obtener contaminantes soportados"""
    try:
        return service.get_supported_pollutants()
    except Exception as e:
        logger.error(f"Error obteniendo contaminantes soportados: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get(
    "/pollutants/{parameter}/info",
    response_model=PollutantInfoDTO,
    summary="Obtener información de un contaminante",
    description="Obtiene información detallada sobre un contaminante específico.",
    responses={
        200: {"description": "Información del contaminante"},
        400: {"description": "Contaminante no soportado"}
    }
)
async def get_pollutant_info(
    parameter: str,
    service: Annotated[AirQualityService, Depends(get_air_quality_service)] = None
) -> Dict[str, Any]:
    """Obtener información de un contaminante específico"""
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
    description="Verifica el estado del servicio de calidad del aire.",
    responses={
        200: {"description": "Servicio funcionando correctamente"}
    }
)
async def health_check(
    service: Annotated[AirQualityService, Depends(get_air_quality_service)] = None
) -> Dict[str, str]:
    """Health check del servicio"""
    return {"status": "ok", "service": "air_quality_monitoring"}
