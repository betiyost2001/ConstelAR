"""
Repositorio TEMPO vía earthaccess: lee variables en 'product/*',
encuentra lat/lon aunque no sean coords, aplica QA y _FillValue,
y recorta bbox dentro del NetCDF.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone, timedelta
from math import cos, radians
from typing import List, Optional, Tuple, Any

import numpy as np
import xarray as xr

from core.logging import get_logger
from utils.exceptions.exceptions import DataSourceError, DataProcessingError
from air_quality_monitoring.domain.models.geo_location import BoundingBox
from air_quality_monitoring.domain.models.measurement import Measurement
from air_quality_monitoring.domain.models.pollutant_data import PollutantRegistry
from air_quality_monitoring.infrastructure.external_apis.earthaccess_client import EarthaccessClient

logger = get_logger("earthaccess_repository")

# -------------------------------------------------------------------
# Flags por .env (valores por defecto)
# -------------------------------------------------------------------
def _env_bool(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "y")

def _env_int(name: str, default: Optional[int] = None) -> Optional[int]:
    v = os.getenv(name)
    if v is None or str(v).strip() == "":
        return default
    try:
        return int(str(v).strip())
    except Exception:
        return default

def _env_float(name: str, default: Optional[float] = None) -> Optional[float]:
    v = os.getenv(name)
    if v is None or str(v).strip() == "":
        return default
    try:
        return float(str(v).strip())
    except Exception:
        return default

TEMPO_USE_OBS_TIME   = _env_bool("TEMPO_USE_OBS_TIME", True)
TEMPO_CLAMP_NEGATIVE = _env_bool("TEMPO_CLAMP_NEGATIVE", True)
TEMPO_DROP_ZERO      = _env_bool("TEMPO_DROP_ZERO", False)
TEMPO_MIN_VALUE      = _env_float("TEMPO_MIN_VALUE", None)    # p.ej. 1e12
TEMPO_THIN           = _env_int("TEMPO_THIN", 1)              # p.ej. 3

# -------------------------------------------------------------------

def _bbox_from_point_radius(lat: float, lon: float, radius_m: int) -> Tuple[float, float, float, float]:
    dlat = radius_m / 111_000.0
    dlon = radius_m / (111_000.0 * max(0.1, cos(radians(lat))))
    return lon - dlon, lat - dlat, lon + dlon, lat + dlat

def _as_utc_iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")

def _isnan(v: Any) -> bool:
    try:
        return np.isnan(v)
    except Exception:
        return False

def _extract_obs_time_dt(ds: xr.Dataset, path: Optional[str] = None) -> datetime:
    """
    Devuelve datetime (UTC) de la observación.
    Prioriza coord 'time'; luego attrs típicos de TEMPO; por último, intenta
    parsear del nombre del archivo; si falla, usa now().
    """
    if not TEMPO_USE_OBS_TIME:
        return datetime.now(timezone.utc)

    # 1) coord time
    try:
        if "time" in ds and getattr(ds["time"], "size", 0):
            t = np.asarray(ds["time"].values).ravel()[0]
            s = np.datetime_as_string(t, unit="s")  # 'YYYY-MM-DDThh:mm:ss'
            if s.endswith("Z"):
                s = s[:-1] + "+00:00"
            if "Z" not in s and "+" not in s and "-" not in s[10:]:
                s += "+00:00"
            return datetime.fromisoformat(s)
    except Exception:
        pass

    # 2) atributos comunes
    for k in (
        "time_coverage_start", "TIME_COVERAGE_START",
        "time_coverage_center", "start_time", "StartTime",
        "datetime", "time_start",
    ):
        v = ds.attrs.get(k)
        if v:
            s = str(v).strip()
            if s.endswith("Z"):
                s = s[:-1] + "+00:00"
            try:
                return datetime.fromisoformat(s)
            except Exception:
                continue

    # 3) intentar con nombre de archivo (formato TEMPO_*_YYYYMMDDThhmmssZ_*.nc)
    try:
        import re, os as _os
        fname = _os.path.basename(str(path or ds.encoding.get("source", "")))
        m = re.search(r"_(\d{8}T\d{6})Z", fname)
        if m:
            return datetime.strptime(m.group(1), "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc)
    except Exception:
        pass

    # 4) fallback
    return datetime.now(timezone.utc)

def _maybe_clamp(val: Any, unit: str, nonneg: bool) -> float:
    """
    Recorta negativos si la unidad es columna (molecules/cm^2 o DU) y nonneg=True.
    """
    try:
        v = float(val)
    except Exception:
        return np.nan
    if not nonneg:
        return v
    unit_norm = (unit or "").strip().lower()
    if unit_norm in ("molecules/cm^2", "du"):
        return float(np.maximum(v, 0.0))
    return v


class NasaEarthaccessRepository:
    """
    Acceso a TEMPO usando earthaccess con soporte de:
      - group="product"
      - lat/lon como variables 2D o 1D (aunque no sean coords del DataArray)
      - máscara por _FillValue/missing_value
      - máscara por main_data_quality_flag == 0
      - recorte por bbox dentro del archivo
      - filtros por valor (clamp negativos, descartar ceros, umbral mínimo)
      - adelgazado de muestreo (thin)
    """

    def __init__(self, client: EarthaccessClient):
        self.client = client
        s = client.settings
        self.pollutant_registry = PollutantRegistry(
            {
                "no2":  (s.tempo_collection_no2,  s.tempo_var_no2),
                "so2":  (getattr(s, "tempo_collection_so2", None), getattr(s, "tempo_var_so2", None)),
                "o3":   (s.tempo_collection_o3,   s.tempo_var_o3),
                "hcho": (s.tempo_collection_hcho, s.tempo_var_hcho),
            }
        )

        # defaults desde .env (se pueden sobreescribir por llamada)
        self._default_nonneg   = TEMPO_CLAMP_NEGATIVE
        self._default_dropzero = TEMPO_DROP_ZERO
        self._default_vmin     = TEMPO_MIN_VALUE
        self._default_thin     = TEMPO_THIN or 1

    def get_pollutant_data(
        self,
        parameter: str,
        bbox: Optional[BoundingBox] = None,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        limit: int = 100,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        radius_m: int = 80_000,
        # filtros opcionales por-request (si None, usa defaults de .env)
        nonneg: Optional[bool] = None,
        dropzero: Optional[bool] = None,
        vmin: Optional[float] = None,
        thin: Optional[int] = None,
    ):
        try:
            if not self.pollutant_registry.is_supported(parameter):
                raise DataSourceError(f"Contaminante no soportado: {parameter}")

            collection_id, variable_path = self.pollutant_registry.get_collection_and_variable(parameter)
            if not collection_id or not variable_path:
                raise DataSourceError(f"Faltan configuración/variables para {parameter}")

            # flags efectivos
            nonneg   = self._default_nonneg   if nonneg   is None else nonneg
            dropzero = self._default_dropzero if dropzero is None else dropzero
            vmin     = self._default_vmin     if vmin     is None else vmin
            thin     = self._default_thin     if thin     is None else (thin or 1)

            # bbox de usuario
            user_bbox: Optional[Tuple[float, float, float, float]] = None
            if bbox:
                user_bbox = (bbox.west, bbox.south, bbox.east, bbox.north)
            elif lat is not None and lon is not None:
                user_bbox = _bbox_from_point_radius(lat, lon, radius_m)
            else:
                raise DataSourceError("Debe proporcionar bbox o lat/lon")

            now = datetime.now(timezone.utc)
            if end is None:
                end = now
            if start is None:
                start = end - timedelta(days=2)

            start_iso, end_iso = _as_utc_iso(start), _as_utc_iso(end)
            logger.info(
                f"[earthaccess:{parameter}] coll={collection_id} var={variable_path} "
                f"bbox=({user_bbox[0]:.3f},{user_bbox[1]:.3f},{user_bbox[2]:.3f},{user_bbox[3]:.3f}) "
                f"window={start_iso}..{end_iso} limit={limit}"
            )

            # 1) buscar + descargar (el cliente ya hace fallback sin bbox si es necesario)
            sr = self.client.search(
                concept_id=collection_id,
                temporal=(start_iso, end_iso),
                bbox=user_bbox,
                max_items=3,
            )
            files = self.client.download(sr.granules)
            if not files:
                logger.info("No se encontraron granules en esa ventana/área (ni sin bbox).")
                from air_quality_monitoring.infrastructure.entities.tempo_response_entity import TempoResponseEntity
                return TempoResponseEntity(source="nasa-tempo", results=[])

            # 2) parsear y muestrear
            measurements: List[Measurement] = []
            for fp in files:
                if len(measurements) >= limit:
                    break
                try:
                    measurements.extend(
                        self._parse_file(
                            path=fp,
                            variable_path=variable_path,
                            parameter=parameter,
                            limit=(limit - len(measurements)),
                            bbox=user_bbox,
                            nonneg=nonneg,
                            dropzero=dropzero,
                            vmin=vmin,
                            thin=thin,
                        )
                    )
                except Exception as e:
                    logger.warning(f"Error leyendo {fp}: {e}", exc_info=True)

            from air_quality_monitoring.infrastructure.entities.tempo_response_entity import TempoResponseEntity
            results = [m.to_list() for m in measurements]
            return TempoResponseEntity(source="nasa-tempo", results=results)

        except Exception as e:
            logger.error("Error earthaccess repository", exc_info=True)
            if isinstance(e, (DataSourceError, DataProcessingError)):
                raise
            raise DataSourceError(f"Error interno: {e}") from e

    # ----------------- helpers -----------------

    def _open_dataset_for_var(self, path: str, variable_path: str) -> Tuple[xr.Dataset, str, Optional[str]]:
        """
        Abre el NetCDF en el grupo correcto si variable_path contiene 'grupo/var'.
        Devuelve (dataset, nombre_variable, nombre_grupo)
        """
        group = None
        varname = variable_path
        if "/" in variable_path:
            parts = variable_path.split("/")
            group = "/".join(parts[:-1]) or None
            varname = parts[-1]

        # preferimos h5netcdf para groups
        try:
            ds = xr.open_dataset(path, engine="h5netcdf", group=group) if group else xr.open_dataset(path, engine="h5netcdf")
        except Exception:
            ds = xr.open_dataset(path, group=group) if group else xr.open_dataset(path)
        return ds, varname, group

    def _find_lat_lon_arrays(
        self,
        path: str,
        group: Optional[str],
        ds: xr.Dataset,
        data_shape: Tuple[int, int]
    ) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], str, str]:
        """
        Busca arrays de lat/lon 1D o 2D (aunque no sean coords del DataArray).
        1) en el propio dataset (grupo actual)
        2) si no están, intenta en 'product' o 'geolocation' o raíz
        Retorna (lat_array, lon_array, lat_name, lon_name)
        """
        lat_keys = ["latitude", "lat", "Latitude"]
        lon_keys = ["longitude", "lon", "Longitude"]

        def _try_in_ds(_ds: xr.Dataset) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], str, str]:
            lat_arr = lon_arr = None
            lat_nm = lon_nm = ""
            for lk in lat_keys:
                if lk in _ds.variables:
                    a = _ds.variables[lk]
                    if a.ndim in (1, 2):
                        lat_arr = a.values
                        lat_nm = lk
                        break
            for lk in lon_keys:
                if lk in _ds.variables:
                    a = _ds.variables[lk]
                    if a.ndim in (1, 2):
                        lon_arr = a.values
                        lon_nm = lk
                        break
            return lat_arr, lon_arr, lat_nm, lon_nm

        # 1) grupo actual
        lat, lon, lat_nm, lon_nm = _try_in_ds(ds)
        if lat is not None and lon is not None:
            return lat, lon, lat_nm, lon_nm

        # 2) 'product'
        if group != "product":
            try:
                dsp = xr.open_dataset(path, engine="h5netcdf", group="product")
                lat, lon, lat_nm, lon_nm = _try_in_ds(dsp)
                dsp.close()
                if lat is not None and lon is not None:
                    return lat, lon, lat_nm, lon_nm
            except Exception:
                pass

        # 3) 'geolocation'
        try:
            dsg = xr.open_dataset(path, engine="h5netcdf", group="geolocation")
            lat, lon, lat_nm, lon_nm = _try_in_ds(dsg)
            dsg.close()
            if lat is not None and lon is not None:
                return lat, lon, lat_nm, lon_nm
        except Exception:
            pass

        # 4) raíz
        try:
            ds0 = xr.open_dataset(path, engine="h5netcdf")
            lat, lon, lat_nm, lon_nm = _try_in_ds(ds0)
            ds0.close()
            if lat is not None and lon is not None:
                return lat, lon, lat_nm, lon_nm
        except Exception:
            pass

        logger.debug("No se hallaron arrays explícitos de lat/lon; usaremos índices.")
        return None, None, "", ""

    def _mask_invalid_values(self, da: xr.DataArray) -> np.ndarray:
        """
        Devuelve máscara booleana de valores válidos (True = válido).
        Considera NaN, _FillValue/missing_value y extremos tipo -9.99e36.
        """
        vals = da.values
        mask = np.ones(vals.shape, dtype=bool)

        mask &= np.isfinite(vals)

        for key in ("_FillValue", "missing_value"):
            fv = da.attrs.get(key)
            if fv is not None:
                try:
                    fv = float(np.array(fv).ravel()[0])
                    mask &= (vals != fv)
                except Exception:
                    pass

        mask &= (vals > -1e30)
        return mask

    def _apply_quality_flag(self, ds: xr.Dataset, group: Optional[str], data_shape: Tuple[int, int], path: str) -> Optional[np.ndarray]:
        """
        Si existe 'main_data_quality_flag' con shape compatible, devuelve máscara válida (True=aceptable).
        Por convención: 0 = bueno.
        """
        qnames = [
            "main_data_quality_flag",
            "data_quality_flag",
            "quality_flag",
            "qa_flag",
        ]
        for qn in qnames:
            if qn in ds.variables:
                qa = ds[qn]
                arr = qa.values
                if qa.ndim == 3 and "time" in qa.dims:
                    try:
                        qa = qa.isel(time=0)
                        arr = qa.values
                    except Exception:
                        arr = arr[0]
                if arr.shape == data_shape:
                    return (arr == 0)

        # buscar en 'product' o 'geolocation'
        for g in ("product", "geolocation"):
            if group == g:
                continue
            try:
                src = ds.encoding.get("source") or path
                dsg = xr.open_dataset(src, engine="h5netcdf", group=g)
                for qn in qnames:
                    if qn in dsg.variables:
                        qa = dsg[qn]
                        arr = qa.values
                        if qa.ndim == 3 and "time" in qa.dims:
                            try:
                                qa = qa.isel(time=0)
                                arr = qa.values
                            except Exception:
                                arr = arr[0]
                        if arr.shape == data_shape:
                            dsg.close()
                            return (arr == 0)
                dsg.close()
            except Exception:
                pass

        return None

    def _parse_file(
        self,
        path: str,
        variable_path: str,
        parameter: str,
        limit: int,
        bbox: Optional[Tuple[float, float, float, float]] = None,
        *,
        nonneg: bool,
        dropzero: bool,
        vmin: Optional[float],
        thin: int,
    ) -> List[Measurement]:
        out: List[Measurement] = []
        ds, varname, group = self._open_dataset_for_var(path, variable_path)

        if varname not in ds.variables and varname not in ds.data_vars:
            logger.warning(f"Variable '{varname}' no encontrada en {path} (varpath='{variable_path}')")
            ds.close()
            return out

        da: xr.DataArray = ds[varname]

        # colapsar tiempo si existe
        if da.ndim == 3:
            if "time" in da.dims:
                da = da.isel(time=0)
            else:
                da = da.isel({da.dims[0]: 0})

        if da.ndim != 2:
            logger.warning(f"Variable '{varname}' dims no-2D tras colapsar time: {da.dims} shape={da.shape}")
            ds.close()
            return out

        ny, nx = da.shape

        # lat/lon aunque no sean coords
        lat_arr, lon_arr, _, _ = self._find_lat_lon_arrays(path, group, ds, (ny, nx))

        # máscaras de validez
        valid_mask = self._mask_invalid_values(da)

        qa_mask = self._apply_quality_flag(ds, group, (ny, nx), path)
        if qa_mask is not None:
            valid_mask &= qa_mask

        vals = da.values
        unit = str(da.attrs.get("units", "")) if da.attrs else ""

        # timestamp de observación
        ts = _extract_obs_time_dt(ds, path)

        # recorte bbox si hay lat/lon
        if bbox and (lat_arr is not None) and (lon_arr is not None):
            west, south, east, north = bbox
            if lat_arr.ndim == 1 and lon_arr.ndim == 1 and lat_arr.size == ny and lon_arr.size == nx:
                lat_sel = (lat_arr >= south) & (lat_arr <= north)
                lon_sel = (lon_arr >= west) & (lon_arr <= east)
                if not np.any(lat_sel) or not np.any(lon_sel):
                    logger.info("Recorte interno por bbox no intersecta lat/lon 1D en este granule.")
                    ds.close()
                    return out
                bbox_mask = np.outer(lat_sel, lon_sel)
            else:
                if lat_arr.shape != (ny, nx) or lon_arr.shape != (ny, nx):
                    logger.debug("lat/lon 2D con shape no compatible; omito recorte por bbox.")
                    bbox_mask = np.ones((ny, nx), dtype=bool)
                else:
                    bbox_mask = (lat_arr >= south) & (lat_arr <= north) & (lon_arr >= west) & (lon_arr <= east)
            valid_mask &= bbox_mask

        total = ny * nx
        valid_count = int(valid_mask.sum())
        logger.debug(f"[{parameter}] {path} -> válidos={valid_count}/{total}")

        if valid_count == 0:
            ds.close()
            return out

        # índices válidos
        ii, jj = np.where(valid_mask)

        # adelgazado opcional
        thin = max(1, int(thin or 1))
        if thin > 1:
            ii = ii[::thin]
            jj = jj[::thin]

        # limitar muestra total
        take = min(limit, ii.size)
        ii = ii[:take]
        jj = jj[:take]

        from air_quality_monitoring.domain.models.geo_location import GeoLocation

        def _lat_of(i, j):
            if lat_arr is None:
                return float(i)
            return float(lat_arr[i] if lat_arr.ndim == 1 else lat_arr[i, j])

        def _lon_of(i, j):
            if lon_arr is None:
                return float(j)
            return float(lon_arr[j] if lon_arr.ndim == 1 else lon_arr[i, j])

        for i, j in zip(ii, jj):
            try:
                raw = vals[i, j]
                if raw is None or _isnan(raw):
                    continue
                value = _maybe_clamp(raw, unit, nonneg=nonneg)
                if _isnan(value):
                    continue
                if dropzero and value == 0.0:
                    continue
                if (vmin is not None) and (value < vmin):
                    continue
                if not np.isfinite(value):
                    continue

                m = Measurement(
                    location=GeoLocation(latitude=_lat_of(i, j), longitude=_lon_of(i, j)),
                    parameter=parameter,
                    value=float(value),
                    unit=unit,
                    timestamp=ts,
                )
                out.append(m)
            except Exception:
                continue

        ds.close()
        return out
