"""
Configuración de endpoints para la API v1
"""
from fastapi import APIRouter
from backend.air_quality_monitoring.api.v1.controllers.air_quality_controller import router as air_quality_router

# Router principal de la API v1
router = APIRouter(prefix="/api/v1")

# Incluir routers de controladores
router.include_router(air_quality_router, prefix="/tempo", tags=["NASA TEMPO"])
