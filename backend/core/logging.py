"""
Sistema de logging centralizado para ConstelAR
"""
import logging
import sys
from typing import Optional
from core.config.config import settings


def setup_logging(log_level: Optional[str] = None) -> logging.Logger:
    """
    Configurar el sistema de logging
    
    Args:
        log_level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Logger configurado
    """
    level = log_level or settings.log_level
    
    # Configurar formato de logs
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configurar handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Configurar logger principal
    logger = logging.getLogger("constelar")
    logger.setLevel(getattr(logging, level.upper()))
    logger.addHandler(console_handler)
    
    # Evitar duplicación de logs
    logger.propagate = False
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Obtener un logger específico
    
    Args:
        name: Nombre del logger
    
    Returns:
        Logger configurado
    """
    return logging.getLogger(f"constelar.{name}")


# Logger principal de la aplicación
main_logger = setup_logging()
