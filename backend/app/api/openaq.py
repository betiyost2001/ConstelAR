# app/api/openaq.py
import requests
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(tags=["openaq"])

OAQ_V2 = "https://api.openaq.org/v2"
OM_AQ  = "https://air-quality-api.open-meteo.com/v1/air-quality"  # sin API key

def _get(url: str, params: dict):
    try:
        r = requests.get(url, params=params, timeout=25)
        r.raise_for_status()
        return r.json()
    except requests.HTTPError as e:
        # Reempaquetamos códigos 5xx/red para arriba, pero dejamos pasar 4xx controlables
        status = getattr(e.response, "status_code", None)
        if status and status in (400, 404, 410, 422):
            raise
        raise HTTPException(status_code=502, detail=f"Upstream error: {e}") from e
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Network error: {e}") from e

# ---------- Helpers de normalización ----------
def _normalize_openaq_measurements(items: list[dict]) -> list[dict]:
    norm: list[dict] = []
    for r in items or []:
        try:
            norm.append({
                "lat": r["coordinates"]["latitude"],
                "lon": r["coordinates"]["longitude"],
                "parameter": r["parameter"],
                "value": r["value"],
                "unit": r.get("unit", ""),
                "datetime": r["date"]["utc"],
            })
        except KeyError:
            continue
    return norm

def _fetch_openmeteo(lat: float, lon: float, limit: int) -> dict:
    om_params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "pm2_5,pm10,ozone,nitrogen_dioxide,sulphur_dioxide,carbon_monoxide",
        "past_days": 1,
        "forecast_days": 0,
    }
    raw = _get(OM_AQ, om_params)
    hourly = raw.get("hourly", {})
    times = hourly.get("time", []) or []
    results: list[dict] = []
    for i, t in enumerate(times):
        for param in ["pm2_5", "pm10", "ozone", "nitrogen_dioxide", "sulphur_dioxide", "carbon_monoxide"]:
            serie = hourly.get(param, [])
            if i < len(serie) and serie[i] is not None:
                results.append({
                    "lat": lat, "lon": lon,
                    "parameter": param, "value": serie[i], "unit": "µg/m³",
                    "datetime": t,
                })
    return {"source": "open-meteo/air-quality", "results": results[:limit]}

# ---------- Endpoints ----------

@router.get("/latest")
def latest(
    city: str | None = Query(None, description="City (opcional)"),
    lat: float | None = Query(None, description="Latitude (opcional)"),
    lon: float | None = Query(None, description="Longitude (opcional)"),
    radius: int = Query(50_000, description="Radius meters (OpenAQ)"),
    limit: int = Query(10, description="Limit"),
):
    """Proxy simple a OpenAQ /latest, con fallback a /measurements."""
    use_coords = (lat is not None and lon is not None)

    # 1) /latest
    try:
        if use_coords:
            q = {"coordinates": f"{lat},{lon}", "radius": radius, "limit": limit}
        elif city:
            q = {"city": city, "limit": limit}
        else:
            q = {"coordinates": "34.0522,-118.2437", "radius": radius, "limit": limit}
        data = _get(f"{OAQ_V2}/latest", q)
        return {"source": "openaq/latest", "query": q, "data": data}
    except HTTPException:
        pass
    except requests.HTTPError:
        pass

    # 2) Fallback /measurements
    mq = {"limit": limit, "order_by": "datetime", "sort": "desc"}
    if use_coords:
        mq.update({"coordinates": f"{lat},{lon}", "radius": radius})
    elif city:
        mq.update({"city": city})
    else:
        mq.update({"coordinates": "34.0522,-118.2437", "radius": radius})
    mdata = _get(f"{OAQ_V2}/measurements", mq)
    return {"source": "openaq/measurements", "query": mq, "data": mdata}

@router.get("/normalized")
def normalized(
    lat: float = Query(-31.4201, description="Latitude"),
    lon: float = Query(-64.1888, description="Longitude"),
    radius: int = Query(50_000, description="Radius meters (OpenAQ)"),
    limit: int = Query(10, description="Limit"),
    city: str | None = Query(None, description="City (optional)"),
):
    """
    Devuelve mediciones normalizadas: [{lat, lon, parameter, value, unit, datetime}]
    Intenta OpenAQ (/measurements) por coords o city; si no hay resultados, fallback a Open-Meteo.
    """
    try:
        mq = {"limit": limit, "order_by": "datetime", "sort": "desc"}
        if city:
            mq["city"] = city
        else:
            mq.update({"coordinates": f"{lat},{lon}", "radius": radius})
        mdata = _get(f"{OAQ_V2}/measurements", mq)
        oa_results = _normalize_openaq_measurements(mdata.get("results", []))
    except Exception:
        oa_results = []

    if oa_results:
        return {"source": "openaq/measurements", "results": oa_results[:limit]}

    # Fallback Open-Meteo
    return _fetch_openmeteo(lat, lon, limit)

@router.get("/measurements")
def measurements(
    bbox: str = Query(..., description="west,south,east,north"),
    pollutant: str = Query("pm25"),
    limit: int = Query(200, ge=1, le=10000),
):
    """
    Devuelve GeoJSON FeatureCollection desde OpenAQ v3 para un bbox.
    """
    try:
        west, south, east, north = map(float, bbox.split(","))
    except Exception:
        raise HTTPException(status_code=400, detail="bbox inválido. Formato: west,south,east,north")

    params = {
        "parameter": pollutant,
        "bbox": f"{west},{south},{east},{north}",
        "limit": limit,
    }
    r = requests.get("https://api.openaq.org/v3/measurements", params=params, timeout=25)
    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail="upstream error")
    data = r.json()

    features = []
    for item in data.get("results", []):
        coord = item.get("coordinates") or {}
        if "latitude" in coord and "longitude" in coord:
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [coord["longitude"], coord["latitude"]]},
                "properties": {
                    "parameter": item.get("parameter"),
                    "value": item.get("value"),
                    "unit": item.get("unit"),
                    "datetime": item.get("date", {}).get("utc"),
                    "sourceName": item.get("sourceName"),
                },
            })
    return {"type": "FeatureCollection", "features": features}
