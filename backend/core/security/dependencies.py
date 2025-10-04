"""
Sistema de inyección de dependencias para ConstelAR
"""
from typing import Annotated
from fastapi import Depends
from backend.core.config.config import get_settings, Settings
from backend.core.logging import get_logger
from backend.air_quality_monitoring.domain.services.air_quality_service import AirQualityService
from backend.air_quality_monitoring.infrastructure.repositories.nasa_harmony_repository import NasaHarmonyRepository
from backend.air_quality_monitoring.infrastructure.external_apis.nasa_harmony_client import NasaHarmonyClient


def get_settings_dependency() -> Settings:
    """Dependencia para obtener configuración"""
    return get_settings()


def get_logger_dependency(name: str):
    """Dependencia para obtener logger"""
    return get_logger(name)


def get_nasa_harmony_client(
    settings: Annotated[Settings, Depends(get_settings_dependency)]
) -> NasaHarmonyClient:
    """Dependencia para cliente NASA Harmony"""
    return NasaHarmonyClient(settings)


def get_nasa_harmony_repository(
    client: Annotated[NasaHarmonyClient, Depends(get_nasa_harmony_client)]
) -> NasaHarmonyRepository:
    """Dependencia para repositorio NASA Harmony"""
    return NasaHarmonyRepository(client)


def get_air_quality_service(
    repository: Annotated[NasaHarmonyRepository, Depends(get_nasa_harmony_repository)]
) -> AirQualityService:
    """Dependencia para servicio de calidad del aire"""
    return AirQualityService(repository)
