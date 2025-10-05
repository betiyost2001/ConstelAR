from functools import lru_cache

from air_quality_monitoring.infrastructure.external_apis.earthaccess_client import EarthaccessClient
from air_quality_monitoring.infrastructure.repositories.nasa_earthaccess_repository import NasaEarthaccessRepository
from air_quality_monitoring.domain.services.air_quality_service import AirQualityService

@lru_cache
def get_earthaccess_client() -> EarthaccessClient:
    return EarthaccessClient()

@lru_cache
def get_earthaccess_repository() -> NasaEarthaccessRepository:
    return NasaEarthaccessRepository(get_earthaccess_client())

def get_air_quality_service() -> AirQualityService:
    return AirQualityService(get_earthaccess_repository())
