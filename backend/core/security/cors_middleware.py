"""
Middleware CORS para ConstelAR
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config.config import settings


def setup_cors_middleware(app: FastAPI) -> None:
    """
    Configurar middleware CORS
    
    Args:
        app: Instancia de FastAPI
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
