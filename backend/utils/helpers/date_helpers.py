"""
Utilidades para manejo de fechas
"""
from datetime import datetime, timedelta, timezone
from typing import Tuple


def utc_iso(dt: datetime) -> str:
    """
    Convertir datetime a string ISO UTC
    
    Args:
        dt: Fecha a convertir
    
    Returns:
        String ISO en formato UTC
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def get_default_time_range() -> Tuple[str, str]:
    """
    Obtener rango de tiempo por defecto (últimas 24 horas)
    
    Returns:
        Tupla con (start_iso, end_iso)
    """
    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=24)
    return utc_iso(start), utc_iso(end)


def parse_datetime_range(start: datetime = None, end: datetime = None) -> Tuple[str, str]:
    """
    Parsear rango de fechas a formato ISO
    
    Args:
        start: Fecha de inicio
        end: Fecha de fin
    
    Returns:
        Tupla con (start_iso, end_iso)
    """
    start_iso = utc_iso(start) if start else None
    end_iso = utc_iso(end) if end else None
    
    if not start_iso or not end_iso:
        return get_default_time_range()
    
    return start_iso, end_iso


def is_valid_time_range(start: datetime, end: datetime) -> bool:
    """
    Validar que el rango de tiempo sea válido
    
    Args:
        start: Fecha de inicio
        end: Fecha de fin
    
    Returns:
        True si el rango es válido
    """
    if start >= end:
        return False
    
    # No permitir rangos muy grandes (más de 30 días)
    if (end - start).days > 30:
        return False
    
    return True
