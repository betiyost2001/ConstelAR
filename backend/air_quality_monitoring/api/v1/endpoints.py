"""
Configuración de endpoints para la API v1
"""
from fastapi import APIRouter
from .controllers.air_quality_controller import router as air_quality_router  # relativo
# o relativo (a prueba de merges):
# from .controllers.air_quality_controller import router as air_quality_router

# Router principal de la API v1
router = APIRouter()

# Incluir routers de controladores
router.include_router(air_quality_router, prefix="/tempo", tags=["NASA TEMPO"])
