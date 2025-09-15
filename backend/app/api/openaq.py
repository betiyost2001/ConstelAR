import requests
import os
from fastapi import APIRouter, HTTPException, Query

router = APIRouter()
OAQ = "https://api.openaq.org/v3"
OMQ = "https://air-quality-api.open-meteo.com/v1/air-quality"  # sin API key

def _get(url, params=None, headers=None):
    # Get API key from environment variable
    api_key = os.getenv("OPENAQ_API_KEY")

    # Prepare headers
    request_headers = {"Accept": "application/json"}
    if api_key and "openaq.org" in url:
        request_headers["X-API-Key"] = api_key
    if headers:
        request_headers.update(headers)

    r = requests.get(url, params=params, headers=request_headers, timeout=25)
    r.raise_for_status()
    return r.json()

@router.get("/latest")
def latest(
    city: str | None = Query(None, description="City (opcional)"),
    lat: float | None = Query(None, description="Latitude (opcional)"),
    lon: float | None = Query(None, description="Longitude (opcional)"),
    radius: int = Query(50_000, description="Radius meters (OpenAQ)"),
    limit: int = Query(10, description="Limit"),
):
    # Preferimos coords si están
    use_coords = (lat is not None and lon is not None)

    # ----- INTENTO 1: OpenAQ v3 /measurements -----
    try:
        mq = {"limit": limit, "order_by": "datetime", "sort": "desc"}
        if use_coords:
            mq.update({"coordinates": f"{lat},{lon}", "radius": radius})
        elif city:
            mq.update({"city": city})
        else:
            # Coordinates updated to USA center
            mq.update({"coordinates": "39.8283,-98.5795", "radius": radius})
        mdata = _get(f"{OAQ}/measurements", mq)
        return {"source": "openaq/measurements", "query": mq, "data": mdata}
    except requests.HTTPError as e:
        status = getattr(e.response, "status_code", None)
        if status not in (400, 401, 403, 404, 410, 422):
            # errores de red/500 → cortar
            raise HTTPException(status_code=502, detail=f"OpenAQ error: {e}") from e

    # ----- INTENTO 3: Open-Meteo Air Quality (sin API key) -----
    # Requiere SI o SI lat/lon → si no vinieron, usa USA center por defecto
    qlat = lat if lat is not None else 39.8283
    qlon = lon if lon is not None else -98.5795
    om_params = {
        "latitude": qlat,
        "longitude": qlon,
        "hourly": "pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,sulphur_dioxide,ozone,aerosol_optical_depth,dust",
        "past_days": 1,
        "forecast_days": 0
    }
    try:
        om = _get(OMQ, om_params)
        # normalizamos una respuesta compacta (último dato horario disponible)
        hourly = om.get("hourly", {})
        # tomar la última entrada disponible por contaminante
        out = []
        if "time" in hourly and hourly["time"]:
            idx = len(hourly["time"]) - 1
            for key in ["pm2_5", "pm10", "ozone", "nitrogen_dioxide", "sulphur_dioxide", "carbon_monoxide"]:
                if key in hourly and len(hourly[key]) > idx and hourly[key][idx] is not None:
                    out.append({
                        "parameter": key,
                        "value": hourly[key][idx],
                        "datetime": hourly["time"][idx],
                        "coordinates": {"latitude": qlat, "longitude": qlon}
                    })
        return {"source": "open-meteo/air-quality", "query": om_params, "data": {"results": out}}
    except requests.RequestException as e3:
        raise HTTPException(status_code=502, detail=f"Open-Meteo error: {e3}") from e3
# --- helpers arriba del router.normalized (podés ponerlos junto a _get) ---
def _normalize_openaq_measurements(items):
    norm = []
    for r in items:
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

def _fetch_openmeteo(lat, lon, limit):
    om_params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "pm2_5,pm10,ozone",
        "past_days": 0,
        "forecast_days": 1,
    }
    raw = _get(OMQ, om_params)
    results = []
    hourly = raw.get("hourly", {})
    times = hourly.get("time", []) or []
    for i, t in enumerate(times):
        for param in ["pm2_5", "pm10", "ozone"]:
            serie = hourly.get(param, [])
            if i < len(serie) and serie[i] is not None:
                results.append({
                    "lat": lat,
                    "lon": lon,
                    "parameter": param,
                    "value": serie[i],
                    "unit": "µg/m³",
                    "datetime": t,
                })
    return {"source": "open-meteo/air-quality", "results": results[:limit]}

# --- endpoint normalized (reemplaza el tuyo) ---
@router.get("/normalized")
def normalized(
    lat: float = Query(39.8283, description="Latitude"),
    lon: float = Query(-98.5795, description="Longitude"),
    radius: int = Query(50_000, description="Radius meters (OpenAQ)"),
    limit: int = Query(10, description="Limit"),
    city: str | None = Query(None, description="City (optional)"),
):
    """
    Devuelve mediciones normalizadas:
    [{lat, lon, parameter, value, unit, datetime}]
    Intenta OpenAQ (/measurements) por coords o city; si 0 resultados, fallback a Open‑Meteo.
    """
    # 1) OpenAQ v3 /measurements (ordena por datetime desc)
    try:
        mq = {"limit": limit, "order_by": "datetime", "sort": "desc"}
        if city:
            mq["city"] = city
        else:
            mq.update({"coordinates": f"{lat},{lon}", "radius": radius})

        mdata = _get(f"{OAQ}/measurements", mq)
        oa_results = _normalize_openaq_measurements(mdata.get("results", []))
    except requests.RequestException as e:
        # Log the error for debugging
        print(f"OpenAQ API error: {e}")
        oa_results = []

    # 2) Si OpenAQ trajo algo, devolver
    if oa_results:
        return {"source": "openaq/measurements", "results": oa_results[:limit]}

    # 3) Fallback a Open‑Meteo si no hay resultados
    return _fetch_openmeteo(lat, lon, limit)
