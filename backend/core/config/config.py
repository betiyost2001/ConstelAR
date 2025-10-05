"""
Configuración global de la aplicación ConstelAR
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "ArgentinaSpace API"
    app_version: str = "1.0.0"
    debug: bool = False

    # Credencial NASA
    harmony_root: str = "https://harmony.earthdata.nasa.gov"
    earthdata_token: Optional[str] = None  # EARTHDATA_TOKEN del .env

    # Colecciones TEMPO (pisables por .env)
    tempo_collection_no2: str = os.getenv("TEMPO_COLLECTION_NO2", "C3685896708-LARC_CLOUD")
    tempo_collection_so2: str = os.getenv("TEMPO_COLLECTION_SO2", "C3685896826-LARC_CLOUD")
    tempo_collection_o3:  str = os.getenv("TEMPO_COLLECTION_O3",  "C3685896625-LARC_CLOUD")
    tempo_collection_hcho:str = os.getenv("TEMPO_COLLECTION_HCHO","C3685897141-LARC_CLOUD")

    # Variables TEMPO (en product/*)
    tempo_var_no2:  str = os.getenv("TEMPO_VAR_NO2",  "product/vertical_column_troposphere")
    tempo_var_so2:  str = os.getenv("TEMPO_VAR_SO2",  "product/column_amount_so2")
    tempo_var_o3:   str = os.getenv("TEMPO_VAR_O3",   "product/column_amount_o3")
    tempo_var_hcho: str = os.getenv("TEMPO_VAR_HCHO", "product/vertical_column")

    cors_origins: list = [
        "http://localhost:5173","http://127.0.0.1:5173",
        "http://localhost:4173","http://127.0.0.1:4173",
        "http://localhost:8080","http://127.0.0.1:8080",
    ]

    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

settings = Settings()

def get_settings() -> Settings:
    return settings
