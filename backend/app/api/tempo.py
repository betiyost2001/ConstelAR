# backend/app/api/tempo.py
from __future__ import annotations

import io
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import numpy as np
import requests
import xarray as xr
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(tags=["NASA TEMPO"])

# ───────────────── helpers de entorno/fechas ─────────────────

def _env(name: str, default: Optional[str] = None) -> Optional[str]:
    v = os.getenv(name)
    return (v.strip() if v else default)

def _utc_iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

def _default_range() -> Tuple[str, str]:
    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=24)
    return _utc_iso(start), _utc_iso(end)

# ───────────────── config ─────────────────

HARMONY_ROOT = _env("HARMONY_ROOT", "https://harmony.earthdata.nasa.gov")

COLL_NO2  = _env("TEMPO_COLLECTION_NO2",  "C2930725014-LARC_CLOUD")
COLL_SO2  = _env("TEMPO_COLLECTION_SO2",  "C2930725337-LARC_CLOUD")
COLL_O3   = _env("TEMPO_COLLECTION_O3",   "C2930725020-LARC_CLOUD")
COLL_HCHO = _env("TEMPO_COLLECTION_HCHO", "C2930725347-LARC_CLOUD")

POLLUTANTS: Dict[str, Tuple[str, str]] = {
    "no2":  (COLL_NO2,  _env("TEMPO_VAR_NO2",  "nitrogendioxide_tropospheric_column")),
    "so2":  (COLL_SO2,  _env("TEMPO_VAR_SO2",  "sulfurdioxide_total_column")),
    "o3":   (COLL_O3,   _env("TEMPO_VAR_O3",   "ozone_total_column")),
    "hcho": (COLL_HCHO, _env("TEMPO_VAR_HCHO", "formaldehyde_tropospheric_column")),
}

EARTHDATA_TOKEN = _env("EARTHDATA_TOKEN")  # obligatorio

def _headers_json() -> Dict[str, str]:
    h = {"Accept": "application/geo+json"}
    if EARTHDATA_TOKEN:
        h["Authorization"] = f"Bearer {EARTHDATA_TOKEN}"
    return h

def _headers_netcdf() -> Dict[str, str]:
    h = {"Accept": "application/x-netcdf"}
    if EARTHDATA_TOKEN:
        h["Authorization"] = f"Bearer {EARTHDATA_TOKEN}"
    return h

ParamsType = Union[Dict[str, Any], Sequence[Tuple[str, Any]]]

def _pick_collection_and_var(parameter: str) -> Tuple[str, str]:
    p = parameter.lower()
    if p not in POLLUTANTS:
        raise HTTPException(status_code=422, detail=f"Parámetro desconocido: {parameter}")
    coll, var = POLLUTANTS[p]
    if not coll or not var:
        raise HTTPException(status_code=422, detail=f"Config faltante para {parameter}")
    return coll, var

# ───────────────── HTTP helpers ─────────────────

def _get_json(url: str, params: ParamsType) -> Dict[str, Any]:
    try:
        r = requests.get(url, params=params, headers=_headers_json(), timeout=90)
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Harmony connection error: {exc}") from exc

    if r.status_code in (401, 403):
        raise HTTPException(status_code=401, detail="Earthdata token/credenciales inválidas o faltantes")
    if r.status_code == 404:
        return {"type": "FeatureCollection", "features": []}
    if r.status_code >= 400:
        raise HTTPException(status_code=502, detail={
            "harmony_error": {"status": r.status_code, "url": r.request.url if r.request else url, "body": r.text[:4000]}
        })
    try:
        return r.json()
    except ValueError:
        return {"type": "FeatureCollection", "features": []}

def _get_netcdf_bytes(url: str, params: ParamsType) -> bytes:
    try:
        r = requests.get(url, params=params, headers=_headers_netcdf(), timeout=180)
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Harmony connection error: {exc}") from exc
    if r.status_code in (401, 403):
        raise HTTPException(status_code=401, detail="Earthdata token/credenciales inválidas o faltantes")
    if r.status_code == 404:
        return b""
    if r.status_code >= 400:
        raise HTTPException(status_code=502, detail={
            "harmony_error": {"status": r.status_code, "url": r.request.url if r.request else url, "body": r.text[:4000]}
        })
    return r.content or b""

# ───────────────── normalización a lista de puntos ─────────────────

def _normalize_geojson(payload: Dict[str, Any], fallback_param: str, limit: int) -> List[List[Any]]:
    feats = payload.get("features") or []
    out: List[List[Any]] = []
    for f in feats:
        if not isinstance(f, dict):
            continue
        geom = f.get("geometry") or {}
        props = f.get("properties") or {}
        if geom.get("type") != "Point":
            continue
        coords = geom.get("coordinates") or []
        if not (isinstance(coords, list) and len(coords) >= 2):
            continue
        lon, lat = float(coords[0]), float(coords[1])
        value = props.get("value") or props.get("measurement") or props.get("mean") or props.get("average")
        unit = props.get("unit") or props.get("units") or ""
        dt = props.get("datetime") or props.get("time") or props.get("timestamp")
        if value is None or dt is None:
            continue
        out.append([lat, lon, fallback_param, value, unit, dt])
        if len(out) >= limit:
            break
    return out

def _sample_grid_to_points(
    ds: xr.Dataset, var: str, parameter: str, limit: int
) -> List[List[Any]]:
    """
    Convierte una grilla (NetCDF) a <= limit puntos:
    - Detecta coords lat/lon (o y/x con attrs)
    - Toma un "thinning" regular para no explotar el front
    - Produce datetime a partir de time si existe
    """
    if var not in ds:
        # variable inexistente
        return []

    # Detectar dims y coords
    da = ds[var]
    # intentar mapeo común
    lat_name = None
    lon_name = None
    for cand in ["lat", "latitude", "y"]:
        if cand in ds.coords:
            lat_name = cand
            break
        if cand in da.dims:
            lat_name = cand
            break
    for cand in ["lon", "longitude", "x"]:
        if cand in ds.coords:
            lon_name = cand
            break
        if cand in da.dims:
            lon_name = cand
            break
    if not lat_name or not lon_name:
        return []

    lat = ds[lat_name].values
    lon = ds[lon_name].values
    arr = da.values

    # Soporte de tiempo (opcional)
    dt_iso = None
    for tname in ["time", "t", "datetime"]:
        if tname in ds.coords:
            try:
                # xarray convierte a np.datetime64
                dt_val = ds[tname].values
                # si es array, tomo el primero
                if isinstance(dt_val, np.ndarray):
                    dt_val = dt_val[0]
                # a ISO
                dt_iso = np.datetime_as_string(dt_val, unit="s")
            except Exception:
                pass
            break

    # Si la variable tiene 3 dims (time, lat, lon), colapsar tiempo en el índice 0
    if arr.ndim == 3:
        arr = arr[0, ...]
    # Si la variable tiene (lat, lon) estamos ok
    if arr.ndim != 2:
        return []

    nlat, nlon = arr.shape
    if nlat < 1 or nlon < 1:
        return []

    # calculo paso para no exceder 'limit'. Queremos un muestreo regular
    # tomamos sqrt(limit) por lado
    k = max(1, int(np.sqrt((nlat * nlon) / max(1, limit))))
    idx_lat = np.arange(0, nlat, k)
    idx_lon = np.arange(0, nlon, k)

    # valor de unidad: imposible saber con certeza desde NetCDF — ponemos por defecto
    unit = ds[var].attrs.get("units", "")

    out: List[List[Any]] = []
    for i in idx_lat:
        for j in idx_lon:
            v = arr[i, j]
            if v is np.nan or v is None:
                continue
            # vectorizar lon/lat según sean coords 1D o 2D
            lat_val = lat[i] if lat.ndim == 1 else lat[i, j]
            lon_val = lon[j] if lon.ndim == 1 else lon[i, j]
            out.append([float(lat_val), float(lon_val), parameter, float(v), unit, dt_iso or ""])
            if len(out) >= limit:
                return out
    return out

# ───────────────── endpoint principal ─────────────────

@router.get("/normalized")
def normalized(
    parameter: str = Query("no2", description="no2|o3|so2|hcho"),
    bbox: Optional[str] = Query(None, description="minLon,minLat,maxLon,maxLat"),
    lat: Optional[float] = Query(None),
    lon: Optional[float] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    start: Optional[datetime] = Query(None, description="UTC ISO"),
    end: Optional[datetime] = Query(None, description="UTC ISO"),
):
    """
    Devuelve mediciones TEMPO normalizadas:
    results: [[lat, lon, parameter, value, unit, datetime], ...]
    1) Intenta GeoJSON (si el servicio publica puntos)
    2) Si no hay features, pide NetCDF, muestrea grilla y devuelve puntos
    """
    coll, var = _pick_collection_and_var(parameter)

    # bbox o punto +/- ~0.2°
    if bbox:
        try:
            west, south, east, north = [float(x.strip()) for x in bbox.split(",")]
        except Exception:
            raise HTTPException(status_code=422, detail="bbox inválido. Formato: minLon,minLat,maxLon,maxLat")
    else:
        if lat is None or lon is None:
            raise HTTPException(status_code=422, detail="Proveé bbox o lat/lon")
        delta = 0.2
        west, south, east, north = (lon - delta, lat - delta, lon + delta, lat + delta)

    start_iso, end_iso = (_utc_iso(start) if start else None, _utc_iso(end) if end else None)
    if not start_iso or not end_iso:
        start_iso, end_iso = _default_range()

    # Ruta A: OGC Coverages (GeoJSON) con rangeSubset
    urlA = f"{HARMONY_ROOT}/ogc-api-coverages/collections/{coll}/coverage/rangeset"
    paramsA: List[Tuple[str, Any]] = [
        ("accept", "application/geo+json"),
        ("datetime", f"{start_iso}/{end_iso}"),
        ("outputCrs", "EPSG:4326"),
        ("count", str(limit)),
        ("subset", f"lon({west}:{east})"),
        ("subset", f"lat({south}:{north})"),
        ("rangeSubset", var),
    ]
    payloadA = _get_json(urlA, paramsA)
    results = _normalize_geojson(payloadA, fallback_param=parameter, limit=limit)
    if results:
        return {"source": "nasa-tempo", "results": results}

    # Ruta B: variable en el path (algunos deployments usan esta convención)
    urlB = f"{HARMONY_ROOT}/{coll}/ogc-api-coverages/1.0.0/{var}/coverage/rangeset"
    paramsB: List[Tuple[str, Any]] = [
        ("accept", "application/geo+json"),
        ("datetime", f"{start_iso}/{end_iso}"),
        ("outputCrs", "EPSG:4326"),
        ("count", str(limit)),
        ("subset", f"lon({west}:{east})"),
        ("subset", f"lat({south}:{north})"),
    ]
    payloadB = _get_json(urlB, paramsB)
    results = _normalize_geojson(payloadB, fallback_param=parameter, limit=limit)
    if results:
        return {"source": "nasa-tempo", "results": results}

    # Ruta C: pedir NetCDF y muestrear grilla → puntos
    # Probamos primero la ruta A con NetCDF (sin rangeSubset/accept JSON)
    paramsNcA: List[Tuple[str, Any]] = [
        ("datetime", f"{start_iso}/{end_iso}"),
        ("outputCrs", "EPSG:4326"),
        ("count", str(limit)),
        ("subset", f"lon({west}:{east})"),
        ("subset", f"lat({south}:{north})"),
        ("rangeSubset", var),
    ]
    nc_bytes = _get_netcdf_bytes(urlA, paramsNcA)
    if not nc_bytes:
        # Intento ruta B NetCDF
        paramsNcB: List[Tuple[str, Any]] = [
            ("datetime", f"{start_iso}/{end_iso}"),
            ("outputCrs", "EPSG:4326"),
            ("count", str(limit)),
            ("subset", f"lon({west}:{east})"),
            ("subset", f"lat({south}:{north})"),
        ]
        nc_bytes = _get_netcdf_bytes(urlB, paramsNcB)

    if nc_bytes:
        try:
            with xr.open_dataset(io.BytesIO(nc_bytes), engine="h5netcdf") as ds:
                sampled = _sample_grid_to_points(ds, var, parameter, limit)
        except Exception as exc:
            # si falla parseo, devolvemos vacío pero sin romper
            sampled = []
    else:
        sampled = []

    return {"source": "nasa-tempo", "results": sampled}
