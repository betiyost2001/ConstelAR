"""
Repositorio para datos de NASA Harmony
"""
import io
from typing import List, Optional, Dict, Any
import xarray as xr
import numpy as np
from backend.core.logging import get_logger
from backend.utils.exceptions.exceptions import DataSourceError, DataProcessingError
from backend.utils.helpers.date_helpers import parse_datetime_range
from backend.utils.helpers.geo_helpers import (
    detect_coordinate_names, calculate_grid_sampling_indices,
    extract_coordinate_values, validate_coordinates
)
from backend.air_quality_monitoring.domain.models.geo_location import BoundingBox
from backend.air_quality_monitoring.domain.models.measurement import Measurement
from backend.air_quality_monitoring.domain.models.pollutant_data import PollutantRegistry
from backend.air_quality_monitoring.infrastructure.external_apis.nasa_harmony_client import NasaHarmonyClient
from backend.air_quality_monitoring.infrastructure.entities.tempo_response_entity import (
    TempoResponseEntity, GeoJsonFeature
)


class NasaHarmonyRepository:
    """Repositorio para acceder a datos de NASA Harmony"""
    
    def __init__(self, client: NasaHarmonyClient):
        """
        Inicializar repositorio
        
        Args:
            client: Cliente NASA Harmony
        """
        self.client = client
        self.logger = get_logger("nasa_harmony_repository")
        
        # Configurar registro de contaminantes
        self.pollutant_registry = PollutantRegistry({
            "no2": (client.settings.tempo_collection_no2, client.settings.tempo_var_no2),
            "so2": (client.settings.tempo_collection_so2, client.settings.tempo_var_so2),
            "o3": (client.settings.tempo_collection_o3, client.settings.tempo_var_o3),
            "hcho": (client.settings.tempo_collection_hcho, client.settings.tempo_var_hcho),
        })
    
    def get_pollutant_data(self, parameter: str, bbox: Optional[BoundingBox] = None,
                          lat: Optional[float] = None, lon: Optional[float] = None,
                          limit: int = 100, start: Optional[str] = None,
                          end: Optional[str] = None) -> TempoResponseEntity:
        """
        Obtener datos de contaminantes
        
        Args:
            parameter: Tipo de contaminante
            bbox: Bounding box geográfico
            lat: Latitud del punto
            lon: Longitud del punto
            limit: Límite de resultados
            start: Fecha de inicio
            end: Fecha de fin
        
        Returns:
            Entidad de respuesta TEMPO
        
        Raises:
            DataSourceError: Error en la fuente de datos
            DataProcessingError: Error en el procesamiento
        """
        try:
            # Validar parámetro
            if not self.pollutant_registry.is_supported(parameter):
                raise DataSourceError(f"Contaminante no soportado: {parameter}")
            
            # Obtener configuración del contaminante
            collection_id, variable_name = self.pollutant_registry.get_collection_and_variable(parameter)
            
            # Determinar área geográfica
            if bbox:
                west, south, east, north = bbox.west, bbox.south, bbox.east, bbox.north
            elif lat is not None and lon is not None:
                if not validate_coordinates(lat, lon):
                    raise DataSourceError(f"Coordenadas inválidas: lat={lat}, lon={lon}")
                bbox = BoundingBox.from_point(lat, lon)
                west, south, east, north = bbox.west, bbox.south, bbox.east, bbox.north
            else:
                raise DataSourceError("Debe proporcionar bbox o lat/lon")
            
            # Parsear fechas
            start_iso, end_iso = parse_datetime_range(
                start, end
            )
            
            # Intentar obtener datos GeoJSON primero
            measurements = self._try_get_geojson_data(
                collection_id, variable_name, parameter,
                west, south, east, north, limit, start_iso, end_iso
            )
            
            # Si no hay datos GeoJSON, intentar NetCDF
            if not measurements:
                measurements = self._try_get_netcdf_data(
                    collection_id, variable_name, parameter,
                    west, south, east, north, limit, start_iso, end_iso
                )
            
            # Convertir mediciones a formato de respuesta
            results = [measurement.to_list() for measurement in measurements]
            
            return TempoResponseEntity(
                source="nasa-tempo",
                results=results
            )
            
        except Exception as e:
            self.logger.error(f"Error obteniendo datos de contaminantes: {e}")
            if isinstance(e, (DataSourceError, DataProcessingError)):
                raise
            raise DataSourceError(f"Error interno: {e}") from e
    
    def _try_get_geojson_data(self, collection_id: str, variable_name: str, parameter: str,
                             west: float, south: float, east: float, north: float,
                             limit: int, start_iso: str, end_iso: str) -> List[Measurement]:
        """Intentar obtener datos GeoJSON"""
        try:
            # Ruta A: OGC Coverages con rangeSubset
            params_a = [
                ("accept", "application/geo+json"),
                ("datetime", f"{start_iso}/{end_iso}"),
                ("outputCrs", "EPSG:4326"),
                ("count", str(limit)),
                ("subset", f"lon({west}:{east})"),
                ("subset", f"lat({south}:{north})"),
                ("rangeSubset", variable_name),
            ]
            
            payload = self.client.get_geojson_data(collection_id, params_a)
            measurements = self._parse_geojson_features(payload, parameter, limit)
            
            if measurements:
                self.logger.info(f"Obtenidos {len(measurements)} datos GeoJSON para {parameter}")
                return measurements
            
            # Ruta B: Variable en el path
            params_b = [
                ("accept", "application/geo+json"),
                ("datetime", f"{start_iso}/{end_iso}"),
                ("outputCrs", "EPSG:4326"),
                ("count", str(limit)),
                ("subset", f"lon({west}:{east})"),
                ("subset", f"lat({south}:{north})"),
            ]
            
            payload = self.client.get_geojson_data_alternative_path(collection_id, variable_name, params_b)
            measurements = self._parse_geojson_features(payload, parameter, limit)
            
            if measurements:
                self.logger.info(f"Obtenidos {len(measurements)} datos GeoJSON (ruta alternativa) para {parameter}")
                return measurements
            
        except Exception as e:
            self.logger.warning(f"Error obteniendo datos GeoJSON: {e}")
        
        return []
    
    def _try_get_netcdf_data(self, collection_id: str, variable_name: str, parameter: str,
                            west: float, south: float, east: float, north: float,
                            limit: int, start_iso: str, end_iso: str) -> List[Measurement]:
        """Intentar obtener datos NetCDF"""
        try:
            # Ruta A: NetCDF con rangeSubset
            params_a = [
                ("datetime", f"{start_iso}/{end_iso}"),
                ("outputCrs", "EPSG:4326"),
                ("count", str(limit)),
                ("subset", f"lon({west}:{east})"),
                ("subset", f"lat({south}:{north})"),
                ("rangeSubset", variable_name),
            ]
            
            nc_bytes = self.client.get_netcdf_data(collection_id, params_a)
            
            if nc_bytes:
                measurements = self._parse_netcdf_data(nc_bytes, variable_name, parameter, limit)
                if measurements:
                    self.logger.info(f"Obtenidos {len(measurements)} datos NetCDF para {parameter}")
                    return measurements
            
            # Ruta B: NetCDF sin rangeSubset
            params_b = [
                ("datetime", f"{start_iso}/{end_iso}"),
                ("outputCrs", "EPSG:4326"),
                ("count", str(limit)),
                ("subset", f"lon({west}:{east})"),
                ("subset", f"lat({south}:{north})"),
            ]
            
            nc_bytes = self.client.get_netcdf_data_alternative_path(collection_id, variable_name, params_b)
            
            if nc_bytes:
                measurements = self._parse_netcdf_data(nc_bytes, variable_name, parameter, limit)
                if measurements:
                    self.logger.info(f"Obtenidos {len(measurements)} datos NetCDF (ruta alternativa) para {parameter}")
                    return measurements
            
        except Exception as e:
            self.logger.warning(f"Error obteniendo datos NetCDF: {e}")
        
        return []
    
    def _parse_geojson_features(self, payload: Dict[str, Any], parameter: str, limit: int) -> List[Measurement]:
        """Parsear features de GeoJSON"""
        measurements = []
        features = payload.get("features", [])
        
        for feature_data in features:
            if len(measurements) >= limit:
                break
                
            try:
                feature = GeoJsonFeature(
                    geometry=feature_data.get("geometry", {}),
                    properties=feature_data.get("properties", {})
                )
                
                if not feature.is_point():
                    continue
                
                coords = feature.get_coordinates()
                if not coords:
                    continue
                
                lon, lat = coords[0], coords[1]
                value = feature.get_value()
                unit = feature.get_unit()
                timestamp_str = feature.get_timestamp()
                
                if value is None or timestamp_str is None:
                    continue
                
                # Crear medición
                from backend.air_quality_monitoring.domain.models.geo_location import GeoLocation
                from datetime import datetime
                
                location = GeoLocation(latitude=lat, longitude=lon)
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                
                measurement = Measurement(
                    location=location,
                    parameter=parameter,
                    value=value,
                    unit=unit,
                    timestamp=timestamp
                )
                
                measurements.append(measurement)
                
            except Exception as e:
                self.logger.warning(f"Error parseando feature GeoJSON: {e}")
                continue
        
        return measurements
    
    def _parse_netcdf_data(self, nc_bytes: bytes, variable_name: str, parameter: str, limit: int) -> List[Measurement]:
        """Parsear datos NetCDF"""
        measurements = []
        
        try:
            with xr.open_dataset(io.BytesIO(nc_bytes), engine="h5netcdf") as ds:
                if variable_name not in ds:
                    self.logger.warning(f"Variable {variable_name} no encontrada en dataset")
                    return measurements
                
                # Detectar nombres de coordenadas
                lat_name, lon_name = detect_coordinate_names(ds)
                if not lat_name or not lon_name:
                    self.logger.warning("No se pudieron detectar coordenadas en el dataset")
                    return measurements
                
                # Obtener datos
                da = ds[variable_name]
                data_values = da.values
                
                # Manejar dimensión de tiempo
                timestamp_str = None
                for tname in ["time", "t", "datetime"]:
                    if tname in ds.coords:
                        try:
                            dt_val = ds[tname].values
                            if isinstance(dt_val, np.ndarray):
                                dt_val = dt_val[0]
                            timestamp_str = np.datetime_as_string(dt_val, unit="s")
                            break
                        except Exception:
                            continue
                
                # Colapsar dimensión de tiempo si existe
                if data_values.ndim == 3:
                    data_values = data_values[0, ...]
                
                if data_values.ndim != 2:
                    self.logger.warning(f"Forma de datos inválida: {data_values.shape}")
                    return measurements
                
                nlat, nlon = data_values.shape
                if nlat < 1 or nlon < 1:
                    return measurements
                
                # Calcular índices de muestreo
                idx_lat, idx_lon = calculate_grid_sampling_indices(nlat, nlon, limit)
                
                # Obtener unidad
                unit = da.attrs.get("units", "")
                
                # Crear mediciones
                from backend.air_quality_monitoring.domain.models.geo_location import GeoLocation
                from datetime import datetime
                
                for i in idx_lat:
                    for j in idx_lon:
                        if len(measurements) >= limit:
                            break
                        
                        value = data_values[i, j]
                        if value is np.nan or value is None:
                            continue
                        
                        try:
                            lat_val, lon_val = extract_coordinate_values(
                                ds, lat_name, lon_name, i, j
                            )
                            
                            location = GeoLocation(latitude=lat_val, longitude=lon_val)
                            timestamp = datetime.fromisoformat(timestamp_str) if timestamp_str else datetime.now()
                            
                            measurement = Measurement(
                                location=location,
                                parameter=parameter,
                                value=float(value),
                                unit=unit,
                                timestamp=timestamp
                            )
                            
                            measurements.append(measurement)
                            
                        except Exception as e:
                            self.logger.warning(f"Error creando medición: {e}")
                            continue
                    
                    if len(measurements) >= limit:
                        break
        
        except Exception as e:
            self.logger.error(f"Error parseando datos NetCDF: {e}")
            raise DataProcessingError(f"Error procesando datos NetCDF: {e}") from e
        
        return measurements
