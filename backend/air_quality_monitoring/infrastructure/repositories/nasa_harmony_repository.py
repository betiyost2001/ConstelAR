"""
Repositorio para datos de NASA Harmony
"""
import io
from datetime import datetime, timezone, timedelta
from math import cos, radians
from typing import List, Optional, Dict, Any

import numpy as np
import xarray as xr

from core.logging import get_logger
from utils.exceptions.exceptions import DataSourceError, DataProcessingError
from utils.helpers.geo_helpers import (
    detect_coordinate_names,
    calculate_grid_sampling_indices,
    extract_coordinate_values,
    validate_coordinates,
)
from air_quality_monitoring.domain.models.geo_location import BoundingBox
from air_quality_monitoring.domain.models.measurement import Measurement
from air_quality_monitoring.domain.models.pollutant_data import PollutantRegistry
from air_quality_monitoring.infrastructure.external_apis.nasa_harmony_client import (
    NasaHarmonyClient,
)
from air_quality_monitoring.infrastructure.entities.tempo_response_entity import (
    TempoResponseEntity,
    GeoJsonFeature,
)

logger = get_logger("nasa_harmony_repository")


# ───────────────────────── Helpers ─────────────────────────

def _bbox_from_point_radius(lat: float, lon: float, radius_m: int):
    """Convierte centro+radio (m) en bbox [west,south,east,north] en grados."""
    dlat = radius_m / 111_000.0
    dlon = radius_m / (111_000.0 * max(0.1, cos(radians(lat))))
    return lon - dlon, lat - dlat, lon + dlon, lat + dlat


def _as_utc_iso(dt: datetime) -> str:
    """Asegura tz UTC y retorna ISO8601 con Z."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")


def _isnan(value: Any) -> bool:
    return isinstance(value, float) and np.isnan(value)


# ─────────────────────── Repositorio ───────────────────────

class NasaHarmonyRepository:
    """Repositorio para acceder a datos de NASA Harmony"""

    def __init__(self, client: NasaHarmonyClient):
        """
        Inicializar repositorio
        Args:
            client: Cliente NASA Harmony
        """
        self.client = client
        self.logger = logger

        # Configurar registro de contaminantes
        self.pollutant_registry = PollutantRegistry(
            {
                "no2": (client.settings.tempo_collection_no2, client.settings.tempo_var_no2),
                "so2": (client.settings.tempo_collection_so2, client.settings.tempo_var_so2),
                "o3": (client.settings.tempo_collection_o3, client.settings.tempo_var_o3),
                "hcho": (client.settings.tempo_collection_hcho, client.settings.tempo_var_hcho),
            }
        )

    def get_pollutant_data(
        self,
        parameter: str,
        bbox: Optional[BoundingBox] = None,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        limit: int = 100,
        start: Optional[datetime] = None,   # datetime (no str)
        end: Optional[datetime] = None,     # datetime (no str)
        radius_m: int = 80_000,             # radio default si vienen lat/lon
    ) -> TempoResponseEntity:
        """
        Obtener datos de contaminantes desde Harmony.

        Args:
            parameter: Tipo de contaminante (no2, so2, o3, hcho)
            bbox: Bounding box geográfico (west,south,east,north)
            lat/lon: Centro de búsqueda (alternativa a bbox)
            limit: Límite de resultados
            start/end: Ventana temporal (datetime)
            radius_m: Radio en metros cuando se usa lat/lon

        Returns:
            TempoResponseEntity con lista de mediciones normalizadas.
        """
        try:
            # Validar parámetro soportado
            if not self.pollutant_registry.is_supported(parameter):
                raise DataSourceError(f"Contaminante no soportado: {parameter}")

            # Colección y variable TEMPO
            collection_id, variable_name = self.pollutant_registry.get_collection_and_variable(parameter)

            # Área geográfica
            if bbox:
                west, south, east, north = bbox.west, bbox.south, bbox.east, bbox.north
            elif lat is not None and lon is not None:
                if not validate_coordinates(lat, lon):
                    raise DataSourceError(f"Coordenadas inválidas: lat={lat}, lon={lon}")
                west, south, east, north = _bbox_from_point_radius(lat, lon, radius_m)
            else:
                raise DataSourceError("Debe proporcionar bbox o lat/lon")

            # Ventana temporal (defaults últimas 48h) y normalización
            now = datetime.now(timezone.utc)
            if end is None:
                end = now
            if start is None:
                start = end - timedelta(days=2)

            start_iso, end_iso = _as_utc_iso(start), _as_utc_iso(end)

            self.logger.info(
                f"[{parameter}] collection={collection_id} var={variable_name} "
                f"bbox=({west:.3f},{south:.3f},{east:.3f},{north:.3f}) "
                f"window={start_iso}..{end_iso} limit={limit}"
            )

            # 1) Intentar GeoJSON (OGC)
            measurements = self._try_get_geojson_data(
                collection_id,
                variable_name,
                parameter,
                west,
                south,
                east,
                north,
                limit,
                start_iso,
                end_iso,
            )

            # 2) NetCDF si no hay features GeoJSON
            if not measurements:
                measurements = self._try_get_netcdf_data(
                    collection_id,
                    variable_name,
                    parameter,
                    west,
                    south,
                    east,
                    north,
                    limit,
                    start_iso,
                    end_iso,
                )

            results = [m.to_list() for m in measurements]
            return TempoResponseEntity(source="nasa-tempo", results=results)

        except Exception as e:
            self.logger.error("Error obteniendo datos de contaminantes", exc_info=True)
            if isinstance(e, (DataSourceError, DataProcessingError)):
                raise
            raise DataSourceError(f"Error interno: {e}") from e

    # ────────────── Rutas GeoJSON (OGC Coverages) ──────────────

    def _try_get_geojson_data(
        self,
        collection_id: str,
        variable_name: str,
        parameter: str,
        west: float,
        south: float,
        east: float,
        north: float,
        limit: int,
        start_iso: str,
        end_iso: str,
    ) -> List[Measurement]:
        """Intentar obtener datos GeoJSON"""
        try:
            # Ruta A: rangeSubset como parámetro
            params_a = [
                ("accept", "application/geo+json"),
                ("datetime", f"{start_iso}/{end_iso}"),
                ("outputCrs", "EPSG:4326"),
                ("count", str(limit)),
                ("subset", f"lon({west}:{east})"),
                ("subset", f"lat({south}:{north})"),
                ("rangeSubset", variable_name),
            ]

            self.logger.info(
                f"GeoJSON A: coll={collection_id} var={variable_name} dt={start_iso}/{end_iso}"
            )
            # ✅ pasar parameter para que el client intente fallback a short-name
            payload = self.client.get_geojson_data(collection_id, params_a, parameter)
            self.logger.info(
                f"GeoJSON A -> type={type(payload).__name__} size~={len(str(payload))}"
            )

            measurements = self._parse_geojson_features(payload, parameter, limit)
            if measurements:
                self.logger.info(f"Obtenidos {len(measurements)} datos GeoJSON para {parameter}")
                return measurements

            # Ruta B: variable en el path
            params_b = [
                ("accept", "application/geo+json"),
                ("datetime", f"{start_iso}/{end_iso}"),
                ("outputCrs", "EPSG:4326"),
                ("count", str(limit)),
                ("subset", f"lon({west}:{east})"),
                ("subset", f"lat({south}:{north})"),
            ]

            self.logger.info(
                f"GeoJSON B: coll={collection_id}/{variable_name} dt={start_iso}/{end_iso}"
            )
            # ✅ alternativa correcta: método alternative_path + parameter
            payload = self.client.get_geojson_data_alternative_path(
                collection_id, variable_name, params_b, parameter
            )
            self.logger.info(
                f"GeoJSON B -> type={type(payload).__name__} size~={len(str(payload))}"
            )

            measurements = self._parse_geojson_features(payload, parameter, limit)
            if measurements:
                self.logger.info(
                    f"Obtenidos {len(measurements)} datos GeoJSON (ruta alternativa) para {parameter}"
                )
                return measurements

        except Exception as e:
            self.logger.warning(f"Error obteniendo datos GeoJSON: {e}")

        return []

    # ─────────────────────── Rutas NetCDF ───────────────────────

    def _try_get_netcdf_data(
        self,
        collection_id: str,
        variable_name: str,
        parameter: str,
        west: float,
        south: float,
        east: float,
        north: float,
        limit: int,
        start_iso: str,
        end_iso: str,
    ) -> List[Measurement]:
        """Intentar obtener datos NetCDF"""
        try:
            # Ruta A: con rangeSubset
            params_a = [
                ("datetime", f"{start_iso}/{end_iso}"),
                ("outputCrs", "EPSG:4326"),
                ("count", str(limit)),
                ("subset", f"lon({west}:{east})"),
                ("subset", f"lat({south}:{north})"),
                ("rangeSubset", variable_name),
            ]

            self.logger.info(
                f"NetCDF A: coll={collection_id} var={variable_name} dt={start_iso}/{end_iso}"
            )
            # ✅ pasar parameter para permitir fallback
            nc_bytes = self.client.get_netcdf_data(collection_id, params_a, parameter)

            if nc_bytes:
                measurements = self._parse_netcdf_data(nc_bytes, variable_name, parameter, limit)
                if measurements:
                    self.logger.info(f"Obtenidos {len(measurements)} datos NetCDF para {parameter}")
                    return measurements

            # Ruta B: sin rangeSubset
            params_b = [
                ("datetime", f"{start_iso}/{end_iso}"),
                ("outputCrs", "EPSG:4326"),
                ("count", str(limit)),
                ("subset", f"lon({west}:{east})"),
                ("subset", f"lat({south}:{north})"),
            ]

            self.logger.info(
                f"NetCDF B: coll={collection_id}/{variable_name} dt={start_iso}/{end_iso}"
            )
            # ✅ alternativa correcta: método alternative_path + parameter
            nc_bytes = self.client.get_netcdf_data_alternative_path(
                collection_id, variable_name, params_b, parameter
            )

            if nc_bytes:
                measurements = self._parse_netcdf_data(nc_bytes, variable_name, parameter, limit)
                if measurements:
                    self.logger.info(
                        f"Obtenidos {len(measurements)} datos NetCDF (ruta alternativa) para {parameter}"
                    )
                    return measurements

        except Exception as e:
            self.logger.warning(f"Error obteniendo datos NetCDF: {e}")

        return []

    # ─────────────────────── Parsers ───────────────────────

    def _parse_geojson_features(
        self, payload: Dict[str, Any], parameter: str, limit: int
    ) -> List[Measurement]:
        """Parsear features de GeoJSON"""
        measurements: List[Measurement] = []
        features = payload.get("features", []) if isinstance(payload, dict) else []

        for feature_data in features:
            if len(measurements) >= limit:
                break

            try:
                feature = GeoJsonFeature(
                    geometry=feature_data.get("geometry", {}),
                    properties=feature_data.get("properties", {}),
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
                if _isnan(value):
                    continue

                # Crear medición
                from air_quality_monitoring.domain.models.geo_location import GeoLocation
                ts = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))

                m = Measurement(
                    location=GeoLocation(latitude=lat, longitude=lon),
                    parameter=parameter,
                    value=float(value),
                    unit=unit or "",
                    timestamp=ts,
                )
                measurements.append(m)

            except Exception as e:
                self.logger.warning(f"Error parseando feature GeoJSON: {e}")
                continue

        return measurements

    def _parse_netcdf_data(
        self, nc_bytes: bytes, variable_name: str, parameter: str, limit: int
    ) -> List[Measurement]:
        """Parsear datos NetCDF"""
        measurements: List[Measurement] = []

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

                da = ds[variable_name]
                data_values = da.values

                # Extraer timestamp si existe
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

                # Índices de muestreo
                idx_lat, idx_lon = calculate_grid_sampling_indices(nlat, nlon, limit)

                unit = da.attrs.get("units", "")

                # Crear mediciones
                from air_quality_monitoring.domain.models.geo_location import GeoLocation

                for i in idx_lat:
                    for j in idx_lon:
                        if len(measurements) >= limit:
                            break

                        value = data_values[i, j]
                        if value is None or _isnan(float(value)):
                            continue

                        try:
                            lat_val, lon_val = extract_coordinate_values(
                                ds, lat_name, lon_name, i, j
                            )
                            ts = (
                                datetime.fromisoformat(timestamp_str)
                                if timestamp_str
                                else datetime.now(timezone.utc)
                            )

                            m = Measurement(
                                location=GeoLocation(latitude=lat_val, longitude=lon_val),
                                parameter=parameter,
                                value=float(value),
                                unit=unit or "",
                                timestamp=ts,
                            )
                            measurements.append(m)

                        except Exception as e:
                            self.logger.warning(f"Error creando medición: {e}")
                            continue

                    if len(measurements) >= limit:
                        break

        except Exception as e:
            self.logger.error(f"Error parseando datos NetCDF: {e}")
            raise DataProcessingError(f"Error procesando datos NetCDF: {e}") from e

        return measurements
    # ────────────── Rutas GeoJSON (OGC Coverages) ──────────────
    def _try_get_geojson_data(
        self,
        collection_id: str,
        variable_name: str,
        parameter: str,
        west: float,
        south: float,
        east: float,
        north: float,
        limit: int,
        start_iso: str,
        end_iso: str,
    ) -> List[Measurement]:
        """Intentar obtener datos GeoJSON (variable en el path)."""
        try:
            params = [
                ("datetime", f"{start_iso}/{end_iso}"),
                ("outputCrs", "EPSG:4326"),
                ("count", str(limit)),
                ("subset", f"lon({west}:{east})"),
                ("subset", f"lat({south}:{north})"),
                # en Coverages la variable va en el path; no es necesario rangeSubset acá
            ]

            self.logger.info(
                f"GeoJSON: coll={collection_id} var={variable_name} dt={start_iso}/{end_iso}"
            )

            # ⚠️ ahora pasamos también variable_name
            payload = self.client.get_geojson_data(
                collection_id=collection_id,
                params=params,
                parameter=parameter,
                variable=variable_name,
            )

            self.logger.info(
                f"GeoJSON -> type={type(payload).__name__} size~={len(str(payload))}"
            )

            measurements = self._parse_geojson_features(payload, parameter, limit)
            if measurements:
                self.logger.info(f"Obtenidos {len(measurements)} datos GeoJSON para {parameter}")
                return measurements

        except Exception as e:
            self.logger.warning(f"Error obteniendo datos GeoJSON: {e}")

        return []

    # ─────────────────────── Rutas NetCDF ───────────────────────
    def _try_get_netcdf_data(
        self,
        collection_id: str,
        variable_name: str,
        parameter: str,
        west: float,
        south: float,
        east: float,
        north: float,
        limit: int,
        start_iso: str,
        end_iso: str,
    ) -> List[Measurement]:
        """Intentar obtener datos NetCDF (variable en el path)."""
        try:
            params = [
                ("datetime", f"{start_iso}/{end_iso}"),
                ("outputCrs", "EPSG:4326"),
                ("count", str(limit)),
                ("subset", f"lon({west}:{east})"),
                ("subset", f"lat({south}:{north})"),
                # igual que arriba: variable va en el path
            ]

            self.logger.info(
                f"NetCDF: coll={collection_id} var={variable_name} dt={start_iso}/{end_iso}"
            )

            # ⚠️ ahora pasamos también variable_name
            nc_bytes = self.client.get_netcdf_data(
                collection_id=collection_id,
                params=params,
                parameter=parameter,
                variable=variable_name,
            )

            if nc_bytes:
                measurements = self._parse_netcdf_data(nc_bytes, variable_name, parameter, limit)
                if measurements:
                    self.logger.info(f"Obtenidos {len(measurements)} datos NetCDF para {parameter}")
                    return measurements

        except Exception as e:
            self.logger.warning(f"Error obteniendo datos NetCDF: {e}")

        return []
