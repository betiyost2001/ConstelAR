# backend/openaq_router.py
from fastapi import APIRouter, HTTPException, Query
import httpx

router = APIRouter(prefix="/openaq", tags=["openaq"])

@router.get("/measurements")
async def measurements(bbox: str = Query(...),
                      pollutant: str = "pm25",
                      limit: int = 200):
    try:
        west, south, east, north = map(float, bbox.split(","))
    except Exception:
        raise HTTPException(status_code=400, detail="bbox inválido")

    # Ejemplo OpenAQ v3 (ajusta si usás otra fuente)
    params = {
        "parameter": pollutant,
        "bbox": f"{west},{south},{east},{north}",
        "limit": limit,
        # agrega fecha, orden, etc. si querés
    }
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get("https://api.openaq.org/v3/measurements", params=params)
    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail="upstream error")

    data = r.json()

    # normalizá a GeoJSON FeatureCollection (ejemplo)
    features = []
    for item in data.get("results", []):
        coord = item.get("coordinates") or {}
        if "latitude" in coord and "longitude" in coord:
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [coord["longitude"], coord["latitude"]],
                },
                "properties": {
                    "parameter": item.get("parameter"),
                    "value": item.get("value"),
                    "unit": item.get("unit"),
                    "datetime": item.get("date", {}).get("utc"),
                    "sourceName": item.get("sourceName"),
                },
            })
    return {"type": "FeatureCollection", "features": features}
