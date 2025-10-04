"""
Excepciones personalizadas para ConstelAR
"""
from typing import Any, Dict, Optional


class ConstelARException(Exception):
    """Excepción base de ConstelAR"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ConfigurationError(ConstelARException):
    """Error de configuración"""
    pass


class DataSourceError(ConstelARException):
    """Error de fuente de datos"""
    pass


class ValidationError(ConstelARException):
    """Error de validación"""
    pass


class NasaHarmonyError(ConstelARException):
    """Error específico de NASA Harmony API"""
    
    def __init__(self, message: str, status_code: Optional[int] = None, 
                 url: Optional[str] = None, response_body: Optional[str] = None):
        details = {}
        if status_code:
            details["status_code"] = status_code
        if url:
            details["url"] = url
        if response_body:
            details["response_body"] = response_body[:4000]  # Limitar tamaño
        
        super().__init__(message, details)
        self.status_code = status_code
        self.url = url
        self.response_body = response_body


class AuthenticationError(ConstelARException):
    """Error de autenticación"""
    pass


class DataProcessingError(ConstelARException):
    """Error de procesamiento de datos"""
    pass


class GeoLocationError(ConstelARException):
    """Error de ubicación geográfica"""
    pass
