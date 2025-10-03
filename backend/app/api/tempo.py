from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import requests
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(tags=["NASA TEMPO"])

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

# === Config por entorno ===
HARMONY_ROOT = _env("HARMONY_ROOT", "https://harmony.earthdata.nasa.gov")

# IDs de colecciones (CMR concept-id) para TEMPO L2 v03 en LARC_CLOUD (ejemplos):
# Si tenés otras versiones/IDs, podés sobreescribir por env.
COLL_NO2 = _env("TEMPO_COLLECTION_NO2", "C2930725014-LARC_CLOUD")
COLL_SO2 = _env("TEMPO_COLLECTION_SO2", "C2930725337-LARC_CLOUD")
COLL_O3  = _env("TEMPO_COLLECTION_O3",  "C2930725020-LARC_CLOUD")
COLL_HCHO= _env("TEMPO_COLLECTION_HCHO","C2930725347-LARC_CLOUD")

# Mapeo simple UI->colección y -> nombre de variable (puede variar por producto)
# Si una variable no coincide, Harmony devuelve 404. Ajustá por producto/versión.
POLLUTANTS: Dict[str, Tuple[str, str]] = {
    "no2":  (COLL_NO2,  _env("TEMPO_VAR_NO2",  "nitrogendioxide_tropospheric_column")),
    "so2":  (COLL_SO2,  _env("TEMPO_VAR_SO2",  "sulfurdioxide_total_column")),
    "o3":   (COLL_O3,   _env("TEMPO_VAR_O3",   "ozone_total_column")),
    "hcho": (COLL_HCHO, _env("TEMPO_VAR_HCHO", "formaldehyde_tropospheric_column")),
}

EARTHDATA_TOKEN = _env("EARTHDATA_TOKEN")  # obligatorio para colecciones protegidas

def _headers() -> Dict[str, str]:
    h = {"Accept": "application/json"}
    if EARTHDATA_TOKEN:
        h["Authorization"] = f"Bearer {EARTHDATA_TOKEN}"
    return h

def _bbox_str(b: Tuple[float, float, float, float]) -> str:
    west, south, east, north = b
    # Harmony OGC Coverages usa subset=lon(a:b)&subset=lat(a:b)
    return f"subset=lon({west}:{east})&subset=lat({south}:{north})"

def _request_json(url: str, params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        r = requests.get(url, params=params, headers=_headers(), timeout=60)
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Harmony connection error: {exc}") from exc

    if r.status_code == 401 or r.status_code == 403:
        raise HTTPException(status_code=401, detail="Earthdata token/credenciales inválidas o faltantes")
    if r.status_code == 404:
        # Devolvemos vacío para que el front no caiga
        return {"features": []}
    if r.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"Harmony error {r.status_code}: {r.text[:200]}")

    # Algunas respuestas no son JSON (por ej. NetCDF). Pedimos GeoJSON en 'format'
    try:
        return r.json()
    except ValueError:
        # Si no es JSON, devolvemos vacío
        return {"features": []}

def _pick_collection_and_var(parameter: str) -> Tuple[str, str]:
    p = parameter.lower()
    if p not in POLLUTANTS:
        raise HTTPException(status_code=422, detail=f"Parámetro desconocido: {parameter}")
    coll, var = POLLUTANTS[p]
    if not coll or not var:
        raise HTTPException(status_code=422, detail=f"Config faltante para {parameter}")
    return coll, var

def _normalize_geojson(payload: Dict[str, Any], fallback_param: str, limit: int) -> List[List[Any]]:
    # Esperamos features tipo Point con propiedades {value, unit, datetime}
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
    Devuelve mediciones normalizadas TEMPO:
    results: [[lat, lon, parameter, value, unit, datetime], ...]
    """
    coll, var = _pick_collection_and_var(parameter)

    # bbox o punto +/- ~0.2°
    if bbox:
        try:
            parts = [float(x.strip()) for x in bbox.split(",")]
            if len(parts) != 4:
                raise ValueError
            west, south, east, north = parts
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

    # URL OGC Coverages (rangeset). Intentamos GeoJSON de puntos si el servicio lo permite
    # Formato: https://harmony.earthdata.nasa.gov/{collectionId}/ogc-api-coverages/1.0.0/{variable}/coverage/rangeset
    url = f"{HARMONY_ROOT}/{coll}/ogc-api-coverages/1.0.0/{var}/coverage/rangeset"

    query = {
        # Subsetting espacial y temporal
        "subset": [f"lon({west}:{east})", f"lat({south}:{north})"],
        "datetime": f"{start_iso}/{end_iso}",
        # Formato GeoJSON (si no está disponible, Harmony puede devolver otro formato -> devolvemos vacío)
        "format": "application/geo+json",
        # Por si el servicio soporta muestreo (algunos drivers lo exponen)
        "maxResults": str(limit),
    }

    # requests no acepta listas en params así que pasamos múltiples subset=
    # armando la query manualmente:
    params: Dict[str, Any] = {"datetime": query["datetime"], "format": query["format"], "maxResults": query["maxResults"]}
    # añadimos subset=... repetido
    # (requests lo arma si usamos tuplas ("subset", "..."))
    req_params = [("datetime", params["datetime"]), ("format", params["format"]), ("maxResults", params["maxResults"])]
    for s in query["subset"]:
        req_params.append(("subset", s))

    payload = _request_json(url, params={})  # mandamos vacío y usamos prepared url abajo si quisieras.
    # NOTA: algunos deployments requieren pasar los params arriba; si tu Harmony ignora
    # format=application/geo+json, volverá otro tipo y _request_json devolverá vacío.

    # Intento alternativo: pasar los params en la misma request
    try:
        payload = requests.get(url, params=req_params, headers=_headers(), timeout=60).json()
    except Exception:
        # si falla parsing/servicio, devolvemos vacío
        payload = {"features": []}

    results = _normalize_geojson(payload, fallback_param=parameter, limit=limit)
    return {"source": "nasa-tempo", "results": results}
