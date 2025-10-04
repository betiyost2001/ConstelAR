"""
Aplicación principal FastAPI para ConstelAR con arquitectura hexagonal
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from core.config.config import get_settings
from core.logging import setup_logging
from core.security.cors_middleware import setup_cors_middleware
from utils.exceptions.exceptions import ConstelARException, ValidationError, DataSourceError
from air_quality_monitoring.api.v1.endpoints import router as v1_router

# Configurar logging
logger = setup_logging()

# Obtener configuración
settings = get_settings()

# Crear aplicación FastAPI
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    ## 🌌 ConstelAR - ArgentinaSpace API
    
    API para monitoreo de calidad del aire utilizando datos satelitales de la misión **NASA TEMPO**.
    
    ### 🎯 Características
    
    - **Datos en tiempo real**: Acceso a mediciones de contaminantes atmosféricos
    - **Múltiples contaminantes**: NO₂, SO₂, O₃, HCHO
    - **Cobertura geográfica**: Datos para Norteamérica con aplicación en Argentina
    - **Arquitectura hexagonal**: Código mantenible y escalable
    - **Documentación completa**: Swagger UI integrado
    
    ### 🌍 Contaminantes Soportados
    
    - **NO₂**: Dióxido de nitrógeno - indicador de emisiones del transporte
    - **SO₂**: Dióxido de azufre - procesos industriales y combustibles
    - **O₃**: Ozono troposférico - reacciones fotoquímicas
    - **HCHO**: Formaldehído - incendios y procesos industriales
    
    ### 🚀 Uso
    
    1. Selecciona el tipo de contaminante
    2. Define el área geográfica (bbox o coordenadas)
    3. Especifica el rango temporal
    4. Obtén mediciones normalizadas
    
    ### 📊 Formato de Respuesta
    
    Las mediciones se devuelven en formato:
    ```json
    {
        "source": "nasa-tempo",
        "results": [
            [lat, lon, parameter, value, unit, timestamp]
        ]
    }
    ```
    
    ### 🔧 Desarrollo
    
    Este proyecto forma parte del **NASA Space Apps Challenge 2025** desarrollado por el equipo argentino **ConstelAR**.
    """,
    contact={
        "name": "Equipo ConstelAR",
        "url": "https://github.com/constelar-team",
        "email": "constelar@argentina.space"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    },
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configurar CORS
setup_cors_middleware(app)

# Configurar logging
logger.info(f"Iniciando {settings.app_name} v{settings.app_version}")

# Incluir routers
app.include_router(v1_router, prefix="/api/v1")

# Endpoint de salud principal
@app.get(
    "/",
    summary="Health Check",
    description="Verifica el estado de la API",
    tags=["Health"]
)
async def health_check():
    """Health check principal de la API"""
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
        "message": "ConstelAR API funcionando correctamente"
    }

# Endpoint de información
@app.get(
    "/info",
    summary="Información de la API",
    description="Obtiene información detallada sobre la API",
    tags=["Info"]
)
async def api_info():
    """Información detallada de la API"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "API para monitoreo de calidad del aire con datos NASA TEMPO",
        "team": "ConstelAR - NASA Space Apps Challenge 2025",
        "country": "Argentina",
        "features": [
            "Datos satelitales NASA TEMPO",
            "Múltiples contaminantes atmosféricos",
            "Arquitectura hexagonal",
            "Documentación Swagger",
            "CORS configurado"
        ],
        "endpoints": {
            "health": "/",
            "info": "/info",
            "docs": "/docs",
            "api": "/api/v1"
        }
    }

# Manejo global de excepciones
@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc: ValidationError):
    """Manejar errores de validación"""
    logger.warning(f"Error de validación: {exc.message}")
    return JSONResponse(
        status_code=400,
        content={
            "error": "ValidationError",
            "message": exc.message,
            "details": exc.details
        }
    )

@app.exception_handler(DataSourceError)
async def data_source_exception_handler(request, exc: DataSourceError):
    """Manejar errores de fuente de datos"""
    logger.error(f"Error de fuente de datos: {exc.message}")
    return JSONResponse(
        status_code=502,
        content={
            "error": "DataSourceError",
            "message": exc.message,
            "details": exc.details
        }
    )

@app.exception_handler(ConstelARException)
async def constelar_exception_handler(request, exc: ConstelARException):
    """Manejar excepciones generales de ConstelAR"""
    logger.error(f"Error ConstelAR: {exc.message}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "ConstelARException",
            "message": exc.message,
            "details": exc.details
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Manejar excepciones generales"""
    logger.error(f"Error interno: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": "Error interno del servidor",
            "details": {"exception": str(exc)} if settings.debug else {}
        }
    )

# Eventos de aplicación
@app.on_event("startup")
async def startup_event():
    """Evento de inicio de la aplicación"""
    logger.info(f"🚀 {settings.app_name} iniciado correctamente")
    logger.info(f"📚 Documentación disponible en: /docs")
    logger.info(f"🔧 Modo debug: {settings.debug}")

@app.on_event("shutdown")
async def shutdown_event():
    """Evento de cierre de la aplicación"""
    logger.info(f"🛑 {settings.app_name} cerrado correctamente")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
