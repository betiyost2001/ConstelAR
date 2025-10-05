from __future__ import annotations

import os
from datetime import datetime, timezone, timedelta
from math import cos, radians
from typing import List, Optional, Tuple, Any
from pathlib import Path # Necesario para las comprobaciones de archivo

import numpy as np
import xarray as xr
import earthaccess 

# -------------------------------------------------------------------
# ⬇️ TUS IMPORTACIONES REALES ⬇️
from core.logging import get_logger 
from utils.exceptions.exceptions import DataSourceError, DataProcessingError
from air_quality_monitoring.domain.models.geo_location import BoundingBox, GeoLocation
from air_quality_monitoring.domain.models.measurement import Measurement
from air_quality_monitoring.domain.models.pollutant_data import PollutantRegistry
from air_quality_monitoring.infrastructure.entities.tempo_response_entity import TempoResponseEntity
# -------------------------------------------------------------------

logger = get_logger("earthaccess_repository")

# -------------------------------------------------------------------
# Flags por .env (valores por defecto) - Usando os.getenv directamente
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

TEMPO_USE_OBS_TIME  = _env_bool("TEMPO_USE_OBS_TIME", True)
TEMPO_CLAMP_NEGATIVE = _env_bool("TEMPO_CLAMP_NEGATIVE", False)
TEMPO_DROP_ZERO = _env_bool("TEMPO_DROP_ZERO", False)
TEMPO_MIN_VALUE = _env_float("TEMPO_MIN_VALUE", None) 
TEMPO_THIN = _env_int("TEMPO_THIN", 1) 

# ... (Funciones auxiliares _bbox_from_point_radius, _as_utc_iso, _isnan, _extract_obs_time_dt, _maybe_clamp se mantienen) ...
def _bbox_from_point_radius(lat: float, lon: float, radius_m: int) -> Tuple[float, float, float, float]:
    dlat = radius_m / 111_000.0
    dlon = radius_m / (111_000.0 * max(0.1, cos(radians(lat))))
    return lon - dlon, lat - dlat, lon + dlon, lat + dlat

def _as_utc_iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')


def _isnan(v: Any) -> bool:
    try:
        return np.isnan(v)
    except Exception:
        return False

def _extract_obs_time_dt(ds: xr.Dataset, path: Optional[str] = None) -> datetime:
    if not TEMPO_USE_OBS_TIME:
        return datetime.now(timezone.utc)
    try:
        if "time" in ds and getattr(ds["time"], "size", 0):
            t = np.asarray(ds["time"].values).ravel()[0]
            s = np.datetime_as_string(t, unit="s")
            if s.endswith("Z"):
                s = s[:-1] + "+00:00"
            if "Z" not in s and "+" not in s and "-" not in s[10:]:
                s += "+00:00"
            return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)
    except Exception:
        pass
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
                return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)
            except Exception:
                continue
    try:
        import re, os as _os
        fname = _os.path.basename(str(path or ds.encoding.get("source", "")))
        m = re.search(r"_(\d{8}T\d{6})Z", fname)
        if m:
            return datetime.strptime(m.group(1), "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc)
    except Exception:
        pass
    return datetime.now(timezone.utc)

def _maybe_clamp(val: Any, unit: str, nonneg: bool) -> float:
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
    
    def __init__(self, client: Any): 
        self.client = client
        s = client.settings
        
        # Mapeo de contaminantes a IDs de Colección y Rutas de Variables
        self.pollutant_registry = PollutantRegistry(
            {
                # Asumo que esta es la configuración FINAL de tu .env:
                "no2": (s.tempo_collection_no2, s.tempo_var_no2),
                "o3":  (s.tempo_collection_o3,  s.tempo_var_o3),
                "hcho": (s.tempo_collection_hcho, s.tempo_var_hcho),
                "no": (s.tempo_collection_no, s.tempo_var_no), # AGREGADO PARA NO
             }
        )

        self._default_nonneg = TEMPO_CLAMP_NEGATIVE
        self._default_dropzero = TEMPO_DROP_ZERO
        self._default_vmin = TEMPO_MIN_VALUE
        self._default_thin = TEMPO_THIN or 1

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
        nonneg: Optional[bool] = None,
        dropzero: Optional[bool] = None,
        vmin: Optional[float] = None,
        thin: Optional[int] = None,
    ) -> TempoResponseEntity:
        try:
            # 1. Validaciones y Configuración
            if not self.pollutant_registry.is_supported(parameter):
                raise DataSourceError(f"Contaminante no soportado: {parameter}")

            collection_id, variable_path = self.pollutant_registry.get_collection_and_variable(parameter)
            if not collection_id or not variable_path:
                raise DataSourceError(f"Faltan configuración/variables para {parameter}")

            nonneg = self._default_nonneg if nonneg is None else nonneg
            dropzero = self._default_dropzero if dropzero is None else dropzero
            vmin = self._default_vmin if vmin is None else vmin
            thin = self._default_thin if thin is None else (thin or 1)

            user_bbox: Optional[Tuple[float, float, float, float]] = None
            if bbox:
                user_bbox = (bbox.west, bbox.south, bbox.east, bbox.north)
            elif lat is not None and lon is not None:
                user_bbox = _bbox_from_point_radius(lat, lon, radius_m)
            else:
                raise DataSourceError("Debe proporcionar bbox o lat/lon") 

            now = datetime.now(timezone.utc)
            end = end or now
            start = start or (end - timedelta(days=2))

            start_iso, end_iso = _as_utc_iso(start), _as_utc_iso(end)
            logger.info(
                f"[earthaccess:{parameter}] coll={collection_id} var={variable_path} "
                f"bbox=({user_bbox[0]:.3f},{user_bbox[1]:.3f},{user_bbox[2]:.3f},{user_bbox[3]:.3f}) "
                f"window={start_iso}..{end_iso} limit={limit}"
            )

            # 2. Búsqueda y Descarga
            max_granules = 3
            sr_list = list(self.client.search( 
                concept_id=collection_id,
                temporal=(start_iso, end_iso),
                bounding_box=user_bbox, 
            ))
            if not sr_list:
                logger.info("No se encontraron granules en esa ventana/área.")
                return TempoResponseEntity(source="nasa-tempo", results=[])
            sr_list = sr_list[:max_granules]
            
            files = self.client.download(sr_list)
            
            # 3. Procesamiento
            valid_files = []
            for fp in files:
                p = Path(fp)
                # Umbral de 1KB para descartar archivos vacíos/de error
                if p.is_file() and p.stat().st_size > 1024: 
                    valid_files.append(fp)
                else:
                    logger.warning(f"Archivo inválido o vacío descartado: {fp}")

            if not valid_files:
                logger.info("No se encontraron archivos válidos para procesar.")
                return TempoResponseEntity(source="nasa-tempo", results=[])

            measurements: List[Measurement] = []
            
            for fp in valid_files:
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
                    # Captura y loguea errores de lectura (h5py, xarray)
                    logger.warning(f"Error leyendo {fp} (posiblemente corrupto o formato incorrecto): {e}", exc_info=True)

            results_list = [m.to_list() for m in measurements]
            return TempoResponseEntity(source="nasa-tempo", results=results_list)

        except Exception as e:
            logger.error("Error earthaccess repository", exc_info=True)
            if isinstance(e, (DataSourceError, DataProcessingError)):
                raise
            # Levantar DataProcessingError para que FastAPI devuelva 500
            raise DataProcessingError(f"Error al acceder/procesar datos TEMPO: {e}") from e

    # ----------------- helpers -----------------

    def _open_dataset_for_var(self, path: str, variable_path: str) -> Tuple[xr.Dataset, str, Optional[str]]:
        group = None
        varname = variable_path
        
        # 1. Intenta separar el grupo HDF5 (ej: 'product') del nombre de la variable.
        if "/" in variable_path:
            parts = variable_path.split("/")
            varname = parts[-1]
            group = "/".join(parts[:-1]) or None

        logger.debug(f"Intentando abrir {path}. Grupo: '{group}', Variable: '{varname}'")

        # 2. Intentar apertura directa con el grupo identificado
        try:
            # Usar 'group' si existe. Si es None, xarray abre la raíz.
            ds = xr.open_dataset(path, engine="h5netcdf", group=group)
        except Exception as e_h5:
            logger.warning(f"Fallo al abrir con h5netcdf y grupo '{group}'. Reintentando sin grupo. Error: {e_h5}")
            
            # 3. Reintento: Sin especificar grupo (a veces la variable está en la raíz)
            try:
                ds = xr.open_dataset(path, engine="h5netcdf", group=None)
                group = None # Si funciona, el grupo es la raíz
            except Exception as e_h5_retry:
                logger.warning(f"Fallo en reintento con h5netcdf. Reintentando con motor predeterminado. Error: {e_h5_retry}")
                
                # 4. Reintento final: Con motor predeterminado (netcdf4) y grupo
                try:
                    ds = xr.open_dataset(path, group=group) 
                except Exception as e_final:
                    logger.error(f"FALLA TOTAL: No se pudo abrir el archivo {path} en ningún formato. {e_final}")
                    ds.close() # Cierre preventivo
                    raise DataProcessingError(f"No se pudo abrir el archivo {path} en formato NetCDF/HDF5.") from e_final

        # 5. Comprobar que la variable existe en el Dataset
        if varname not in ds.variables:
             # Si falla, prueba a usar la ruta completa como nombre de la variable.
            if variable_path in ds.variables:
                varname = variable_path
            else:
                ds.close()
                raise DataProcessingError(f"La variable '{varname}' o '{variable_path}' no se encontró en el dataset.")
        
        return ds, varname, group


    def _find_lat_lon_arrays(
        self,
        path: str,
        group: Optional[str],
        ds: xr.Dataset,
        data_shape: Tuple[int, int]
    ) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], str, str]:
        lat_keys = ["latitude", "lat", "Latitude"]
        lon_keys = ["longitude", "lon", "Longitude"]

        def _try_in_ds(_ds: xr.Dataset) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], str, str]:
            lat_arr = lon_arr = None
            lat_nm = lon_nm = ""
            for lk in lat_keys:
                if lk in _ds.variables:
                    a = _ds.variables[lk]
                    # Solo considerar arrays de 1 o 2 dimensiones
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
            
            # Verificación crucial: Las coordenadas deben coincidir con la forma de los datos
            if lat_arr is not None and lon_arr is not None:
                is_2d_match = lat_arr.ndim == 2 and lat_arr.shape == data_shape
                is_1d_match = (
                    lat_arr.ndim == 1 and lon_arr.ndim == 1 and 
                    lat_arr.size == data_shape[0] and lon_arr.size == data_shape[1]
                )
                
                if not (is_2d_match or is_1d_match):
                    logger.debug(f"Lat/Lon shape mismatch: {lat_arr.shape} vs data {data_shape}. Discarding.")
                    return None, None, "", ""
            elif lat_arr is not None or lon_arr is not None:
                # Solo se encontró una coordenada
                return None, None, "", ""
                
            return lat_arr, lon_arr, lat_nm, lon_nm

        # 1. Buscar en el dataset principal (ds)
        lat, lon, lat_nm, lon_nm = _try_in_ds(ds)
        if lat is not None and lon is not None:
            logger.debug(f"Lat/Lon encontradas en el grupo principal.")
            return lat, lon, lat_nm, lon_nm

        # 2. Intentar en grupos de geolocalización comunes
        # NOTA: Este bloque de reintento es CRÍTICO para TEMPO
        for g_try in ("geolocation", "product/geolocation", "/geolocation", "/"):
            # Evitar reabrir el grupo que ya probamos
            if g_try == group: continue
            
            try:
                # Abrir el dataset desde el archivo, especificando el nuevo grupo
                dsp = xr.open_dataset(path, engine="h5netcdf", group=g_try)
                lat, lon, lat_nm, lon_nm = _try_in_ds(dsp)
                dsp.close()
                if lat is not None and lon is not None:
                    logger.debug(f"Lat/Lon encontradas en grupo: {g_try}")
                    return lat, lon, lat_nm, lon_nm
            except Exception as e:
                # Fallo al abrir el grupo o al no encontrar variables. Es normal.
                logger.debug(f"Fallo al buscar lat/lon en grupo {g_try}: {e}")
                pass 

        logger.warning("No se hallaron arrays explícitos de lat/lon con forma compatible.")
        return None, None, "", ""

    # ... (el resto de funciones auxiliares se mantiene sin cambios) ...

    def _mask_invalid_values(self, da: xr.DataArray) -> np.ndarray:
        # ... (implementación anterior) ...
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
        # ... (implementación anterior) ...
        qnames = ["main_data_quality_flag", "data_quality_flag", "quality_flag", "qa_flag"]
        for qn in qnames:
            if qn in ds.variables:
                qa = ds[qn]
                arr = qa.values
                if arr.shape == data_shape:
                    return (arr == 0)
        
        for g in ("product", "geolocation", None):
            if group == g: continue
            try:
                src = ds.encoding.get("source") or path
                dsg = xr.open_dataset(src, engine="h5netcdf", group=g)
                for qn in qnames:
                    if qn in dsg.variables:
                        qa = dsg[qn]
                        arr = qa.values
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
            logger.warning(f"Variable '{varname}' no encontrada en {path}")
            ds.close()
            return out

        da: xr.DataArray = ds[varname]

        # MODIFICACIÓN CLAVE: Lógica robusta para colapsar arrays > 2D
        if da.ndim > 2:
            
            # PRIORIDAD 1: Intenta eliminar la dimensión 'time' si existe y solo hay 3 o 4 dimensiones
            if "time" in da.dims and da.ndim in (3, 4):
                da = da.isel(time=0, drop=True)
            
            # PRIORIDAD 2: Si el array sigue siendo 3D, intenta colapsar la PRIMERA dimensión restante
            # Esto maneja capas verticales (Layer) que a menudo son la primera dimensión.
            if da.ndim == 3:
                first_dim_name = da.dims[0]
                da = da.isel({first_dim_name: 0}, drop=True)
            
            # Verificación final: Si no es 2D, hay un problema
            if da.ndim != 2:
                 logger.warning(
                    f"Variable '{varname}' dims no-2D ({da.ndim}D) tras colapsar. "
                    f"Shape: {da.shape}"
                 )
                 ds.close()
                 return out
        
        # Si tiene 2 dimensiones, continuamos
        if da.ndim != 2:
            logger.warning(f"Variable '{varname}' dims no-2D: {da.dims} shape={da.shape}")
            ds.close()
            return out


        ny, nx = da.shape
        lat_arr, lon_arr, _, _ = self._find_lat_lon_arrays(path, group, ds, (ny, nx))
        
        # Si no se encuentran coordenadas, no podemos mapear los datos
        if lat_arr is None or lon_arr is None:
             logger.warning(f"No se pudieron encontrar coordenadas (Lat/Lon) compatibles para {path}. Descartando.")
             ds.close()
             return out

        valid_mask = self._mask_invalid_values(da)
        qa_mask = self._apply_quality_flag(ds, group, (ny, nx), path)
        if qa_mask is not None:
            valid_mask &= qa_mask

        vals = da.values
        unit = str(da.attrs.get("units", "")) if da.attrs else ""
        ts = _extract_obs_time_dt(ds, path)

        # Aplicar máscara de BBox
        if bbox:
            west, south, east, north = bbox
            if lat_arr.ndim == 1 and lon_arr.ndim == 1 and lat_arr.size == ny and lon_arr.size == nx:
                # Grid 1D (vector)
                lat_sel = (lat_arr >= south) & (lat_arr <= north)
                lon_sel = (lon_arr >= west) & (lon_arr <= east)
                bbox_mask = np.outer(lat_sel, lon_sel)
            elif lat_arr.shape == (ny, nx) and lon_arr.shape == (ny, nx):
                # Grid 2D (matrices)
                bbox_mask = (lat_arr >= south) & (lat_arr <= north) & (lon_arr >= west) & (lon_arr <= east)
            else:
                # Esto no debería pasar si _find_lat_lon_arrays funciona
                logger.debug("Lat/Lon 2D con forma no compatible; omito recorte por bbox.")
                bbox_mask = np.ones((ny, nx), dtype=bool)
                
            valid_mask &= bbox_mask

        if valid_mask.sum() == 0:
            ds.close()
            return out

        ii, jj = np.where(valid_mask)
        thin = max(1, int(thin or 1))
        if thin > 1:
            ii = ii[::thin]
            jj = jj[::thin]

        take = min(limit, ii.size)
        ii = ii[:take]
        jj = jj[:take]

        # Definiciones para extracción de coordenadas (funciona para 1D y 2D)
        def _lat_of(i, j):
            # lat_arr es 1D (vector) o 2D (matriz)
            return float(lat_arr[i] if lat_arr.ndim == 1 else lat_arr[i, j])

        def _lon_of(i, j):
            # lon_arr es 1D (vector) o 2D (matriz)
            # Nota: Si lat/lon son 1D, lat usa i (filas) y lon usa j (columnas)
            return float(lon_arr[j] if lon_arr.ndim == 1 else lon_arr[i, j])

        for i, j in zip(ii, jj):
            try:
                raw = vals[i, j]
                if raw is None or _isnan(raw): continue
                value = _maybe_clamp(raw, unit, nonneg=nonneg)
                if _isnan(value) or not np.isfinite(value): continue
                if dropzero and value == 0.0: continue
                if (vmin is not None) and (value < vmin): continue

                m = Measurement(
                    location=GeoLocation(latitude=_lat_of(i, j), longitude=_lon_of(i, j)),
                    parameter=parameter,
                    value=float(value),
                    unit=unit,
                    timestamp=ts,
                )
                out.append(m)
            except Exception:
                # Este catch evita que un punto malo colapse el loop completo
                continue

        ds.close()
        return out