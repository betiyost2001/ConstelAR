"""
Configuración global de la aplicación ConstelAR
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuración de la aplicación"""
    
    # Configuración de la aplicación
    app_name: str = "ArgentinaSpace API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Configuración de NASA TEMPO
    harmony_root: str = "https://harmony.earthdata.nasa.gov"
    earthdata_token: Optional[str] = None
    
    # Colecciones TEMPO
    tempo_collection_no2: str = "C2930725014-LARC_CLOUD"
    tempo_collection_so2: str = "C2930725337-LARC_CLOUD"
    tempo_collection_o3: str = "C2930725020-LARC_CLOUD"
    tempo_collection_hcho: str = "C2930725347-LARC_CLOUD"
    
    # Variables TEMPO
    tempo_var_no2: str = "nitrogendioxide_tropospheric_column"
    tempo_var_so2: str = "sulfurdioxide_total_column"
    tempo_var_o3: str = "ozone_total_column"
    tempo_var_hcho: str = "formaldehyde_tropospheric_column"
    
    # Configuración de CORS
    cors_origins: list = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ]
    
    # Configuración de logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignorar variables extra no definidas


# Instancia global de configuración
settings = Settings()


def get_settings() -> Settings:
    """Obtener configuración de la aplicación"""
    return settings
