from functools import lru_cache

from air_quality_monitoring.infrastructure.external_apis.nasa_harmony_client import NasaHarmonyClient
from air_quality_monitoring.infrastructure.repositories.nasa_harmony_repository import NasaHarmonyRepository
from air_quality_monitoring.domain.services.air_quality_service import AirQualityService

@lru_cache
def get_nasa_harmony_client() -> NasaHarmonyClient:
    # 👇 ya NO le pasamos settings
    return NasaHarmonyClient()

@lru_cache
def get_nasa_harmony_repository() -> NasaHarmonyRepository:
    return NasaHarmonyRepository(get_nasa_harmony_client())

def get_air_quality_service() -> AirQualityService:
    return AirQualityService(get_nasa_harmony_repository())
