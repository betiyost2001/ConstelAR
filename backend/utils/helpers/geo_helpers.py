"""
Utilidades para manejo de datos geográficos
"""
import numpy as np
from typing import List, Any, Tuple
from backend.air_quality_monitoring.domain.models.geo_location import GeoLocation, BoundingBox


def validate_coordinates(lat: float, lon: float) -> bool:
    """
    Validar coordenadas geográficas
    
    Args:
        lat: Latitud
        lon: Longitud
    
    Returns:
        True si las coordenadas son válidas
    """
    return (-90 <= lat <= 90) and (-180 <= lon <= 180)


def calculate_grid_sampling_indices(nlat: int, nlon: int, limit: int) -> Tuple[List[int], List[int]]:
    """
    Calcular índices para muestreo regular de grilla
    
    Args:
        nlat: Número de filas de latitud
        nlon: Número de columnas de longitud
        limit: Límite máximo de puntos
    
    Returns:
        Tupla con (indices_lat, indices_lon)
    """
    if nlat < 1 or nlon < 1:
        return [], []
    
    # Calcular paso para no exceder 'limit'
    # Tomamos sqrt(limit) por lado para muestreo regular
    k = max(1, int(np.sqrt((nlat * nlon) / max(1, limit))))
    
    idx_lat = np.arange(0, nlat, k).tolist()
    idx_lon = np.arange(0, nlon, k).tolist()
    
    return idx_lat, idx_lon


def extract_coordinate_values(dataset, lat_name: str, lon_name: str, 
                            lat_idx: int, lon_idx: int) -> Tuple[float, float]:
    """
    Extraer valores de coordenadas de un dataset
    
    Args:
        dataset: Dataset con coordenadas
        lat_name: Nombre de la dimensión de latitud
        lon_name: Nombre de la dimensión de longitud
        lat_idx: Índice de latitud
        lon_idx: Índice de longitud
    
    Returns:
        Tupla con (lat_value, lon_value)
    """
    lat_values = dataset[lat_name].values
    lon_values = dataset[lon_name].values
    
    # Manejar coordenadas 1D o 2D
    lat_val = lat_values[lat_idx] if lat_values.ndim == 1 else lat_values[lat_idx, lon_idx]
    lon_val = lon_values[lon_idx] if lon_values.ndim == 1 else lon_values[lat_idx, lon_idx]
    
    return float(lat_val), float(lon_val)


def detect_coordinate_names(dataset) -> Tuple[str, str]:
    """
    Detectar nombres de coordenadas en un dataset
    
    Args:
        dataset: Dataset a analizar
    
    Returns:
        Tupla con (lat_name, lon_name)
    """
    lat_candidates = ["lat", "latitude", "y"]
    lon_candidates = ["lon", "longitude", "x"]
    
    lat_name = None
    lon_name = None
    
    # Buscar coordenadas de latitud
    for candidate in lat_candidates:
        if candidate in dataset.coords:
            lat_name = candidate
            break
        if candidate in dataset.dims:
            lat_name = candidate
            break
    
    # Buscar coordenadas de longitud
    for candidate in lon_candidates:
        if candidate in dataset.coords:
            lon_name = candidate
            break
        if candidate in dataset.dims:
            lon_name = candidate
            break
    
    return lat_name, lon_name


def create_location_from_coordinates(lat: float, lon: float) -> GeoLocation:
    """
    Crear ubicación geográfica desde coordenadas
    
    Args:
        lat: Latitud
        lon: Longitud
    
    Returns:
        Ubicación geográfica
    """
    return GeoLocation(latitude=lat, longitude=lon)


def create_bbox_from_point(lat: float, lon: float, delta: float = 0.2) -> BoundingBox:
    """
    Crear bounding box desde un punto
    
    Args:
        lat: Latitud del punto
        lon: Longitud del punto
        delta: Delta para crear el bounding box
    
    Returns:
        Bounding box
    """
    return BoundingBox.from_point(lat, lon, delta)
