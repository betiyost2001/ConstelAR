"""NASA TEMPO air quality client and FastAPI router."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, MutableMapping, Optional, Tuple

import requests
from fastapi import APIRouter, HTTPException, Query


class EarthdataAuthError(RuntimeError):
    """Raised when Earthdata authentication fails."""


class NasaTempoInvalidQuery(ValueError):
    """Raised when the query sent to the NASA TEMPO API is invalid."""


class NasaTempoServiceError(RuntimeError):
    """Raised for unexpected NASA TEMPO service errors."""


def _env(name: str) -> Optional[str]:
    value = os.getenv(name)
    if value:
        value = value.strip()
    return value or None


def _default_time_range() -> Tuple[datetime, datetime]:
    """Return the default [start, end] time range (last 24 hours UTC)."""

    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=24)
    return start, end


def _parse_bbox(bbox: str) -> Tuple[float, float, float, float]:
    try:
        parts = [float(p.strip()) for p in bbox.split(",")]
    except ValueError as exc:  # non numeric
        raise NasaTempoInvalidQuery(
            "BBox must contain comma separated numeric values"
        ) from exc

    if len(parts) != 4:
        raise NasaTempoInvalidQuery(
            "BBox must contain exactly four numbers: minLon,minLat,maxLon,maxLat"
        )

    min_lon, min_lat, max_lon, max_lat = parts
    if min_lon >= max_lon or min_lat >= max_lat:
        raise NasaTempoInvalidQuery(
            "BBox coordinates are not valid (check min/max values)"
        )

    return min_lon, min_lat, max_lon, max_lat


def _format_datetime(value: datetime | None) -> Optional[str]:
    if value is None:
        return None
    if value.tzinfo is None:
        # Assume UTC if no timezone supplied
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class NasaTempoClient:
    """HTTP client to interact with NASA TEMPO API endpoints."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        dataset: Optional[str] = None,
        timeout: float | int = 30,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.base_url = (
            base_url
            or _env("NASA_TEMPO_BASE_URL")
            or "https://harmony.earthdata.nasa.gov/tempo"
        ).rstrip("/")
        self.dataset = dataset or _env("NASA_TEMPO_DATASET") or "tempo_no2_l2_reduced"
        self.timeout = float(timeout)
        self.session = session or requests.Session()
        token = (
            _env("EARTHDATA_TOKEN")
            or _env("NASA_EARTHDATA_TOKEN")
            or _env("HARMONY_AUTH_TOKEN")
        )
        self._token = token

        username = _env("EARTHDATA_USERNAME")
        password = _env("EARTHDATA_PASSWORD")
        if username and password:
            self.session.auth = (username, password)

        self._api_key = _env("NASA_TEMPO_API_KEY")

    def _headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {"Accept": "application/json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        if self._api_key:
            headers["X-Api-Key"] = self._api_key
        return headers

    def _request(
        self, method: str, path: str, params: MutableMapping[str, Any]
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        try:
            response = self.session.request(
                method,
                url,
                params=params,
                headers=self._headers(),
                timeout=self.timeout,
            )
        except requests.Timeout as exc:
            raise NasaTempoServiceError("NASA TEMPO service timeout") from exc
        except requests.RequestException as exc:
            raise NasaTempoServiceError(
                f"NASA TEMPO service connection error: {exc}"
            ) from exc

        if response.status_code in (401, 403):
            raise EarthdataAuthError(
                "NASA Earthdata authentication failed (check token/credentials)"
            )
        if response.status_code == 404:
            raise NasaTempoInvalidQuery("Requested NASA TEMPO resource was not found")
        if response.status_code >= 400:
            raise NasaTempoServiceError(
                f"NASA TEMPO service error {response.status_code}: {response.text.strip() or response.reason}"
            )

        try:
            data: Dict[str, Any] = response.json()
        except ValueError as exc:
            raise NasaTempoServiceError(
                "NASA TEMPO response is not valid JSON"
            ) from exc

        return data

    def measurements(
        self,
        *,
        parameter: str,
        limit: int,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        radius_km: Optional[float] = None,
        bbox: Optional[Tuple[float, float, float, float]] = None,
    ) -> Dict[str, Any]:
        if bbox is None and (lat is None or lon is None):
            raise NasaTempoInvalidQuery(
                "Provide either latitude/longitude or a bounding box"
            )

        params: Dict[str, Any] = {
            "parameter": parameter,
            "limit": max(1, min(limit, 500)),
            "dataset": self.dataset,
        }

        start_iso = _format_datetime(start)
        end_iso = _format_datetime(end)
        if start_iso:
            params["start"] = start_iso
        if end_iso:
            params["end"] = end_iso

        if bbox is not None:
            params["bbox"] = ",".join(str(x) for x in bbox)
        else:
            params["latitude"] = lat
            params["longitude"] = lon
            if radius_km is not None:
                params["radius"] = float(radius_km)

        # Harmony exposes an observations endpoint for gridded subsets.
        # Documentation references: https://harmony.earthdata.nasa.gov/
        return self._request("GET", "observations", params)


def _extract_candidate_iterable(payload: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    for key in ("observations", "results", "features", "items", "data"):
        value = payload.get(key)
        if isinstance(value, list):
            return value
    # Some responses embed observations under a "properties" object
    if "properties" in payload and isinstance(payload["properties"], dict):
        inner = payload["properties"].get("observations")
        if isinstance(inner, list):
            return inner
    return []


def _normalize_measurements(
    payload: Dict[str, Any],
    *,
    fallback_parameter: str,
    limit: int,
) -> List[Dict[str, Any]]:
    items = _extract_candidate_iterable(payload)
    normalized: List[Dict[str, Any]] = []

    for item in items:
        if not isinstance(item, dict):
            continue

        props: Dict[str, Any] = (
            item.get("properties", {})
            if isinstance(item.get("properties"), dict)
            else {}
        )
        geom = item.get("geometry") if isinstance(item.get("geometry"), dict) else {}

        coords = (
            geom.get("coordinates")
            if isinstance(geom.get("coordinates"), (list, tuple))
            else None
        )
        lat = props.get("latitude")
        lon = props.get("longitude")
        if lat is None and coords and len(coords) >= 2:
            lon = coords[0]
            lat = coords[1]
        elif lon is None and coords and len(coords) >= 2:
            lon = coords[0]

        parameter = (
            props.get("parameter") or item.get("parameter") or fallback_parameter
        )

        # Determine the value and units.
        value = (
            props.get("value")
            or props.get("measurement")
            or props.get("average")
            or props.get("mean")
            or item.get("value")
            or item.get("measurement")
        )

        unit = props.get("unit") or props.get("units") or item.get("unit") or ""

        dt = (
            props.get("time")
            or props.get("datetime")
            or props.get("timestamp")
            or props.get("start_time")
            or props.get("start_datetime")
            or item.get("datetime")
            or item.get("time")
        )

        if lat is None or lon is None or value is None or dt is None:
            continue

        normalized.append(
            [
                float(lat),
                float(lon),
                str(parameter),
                value,
                unit,
                dt,
            ]
        )

        if len(normalized) >= limit:
            break

    return normalized


router = APIRouter(tags=["NASA TEMPO"])
client = NasaTempoClient()


@router.get("/normalized")
def normalized(
    parameter: str = Query(
        "no2", description="Pollutant parameter identifier (e.g. no2, o3, so2)"
    ),
    lat: Optional[float] = Query(None, description="Latitude for point queries"),
    lon: Optional[float] = Query(None, description="Longitude for point queries"),
    bbox: Optional[str] = Query(
        None,
        description="Bounding box as minLon,minLat,maxLon,maxLat (overrides lat/lon if provided)",
    ),
    radius_km: Optional[float] = Query(
        None,
        description="Radius in kilometers around the point location (when using lat/lon)",
        ge=0.0,
    ),
    start: Optional[datetime] = Query(
        None,
        description="Start datetime (UTC). Defaults to 24 hours before `end`.",
    ),
    end: Optional[datetime] = Query(
        None, description="End datetime (UTC). Defaults to now."
    ),
    limit: int = Query(
        50, ge=1, le=500, description="Maximum number of measurements to return"
    ),
):
    """Return normalized TEMPO pollutant measurements for a location or bounding box."""

    bbox_tuple: Optional[Tuple[float, float, float, float]] = None
    if bbox:
        try:
            bbox_tuple = _parse_bbox(bbox)
        except NasaTempoInvalidQuery as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    if bbox_tuple is None and (lat is None or lon is None):
        raise HTTPException(status_code=422, detail="Provide either lat/lon or bbox")

    if end is None:
        _, default_end = _default_time_range()
        end = default_end
    if start is None:
        default_start, _ = _default_time_range()
        start = default_start

    try:
        payload = client.measurements(
            parameter=parameter,
            limit=limit,
            start=start,
            end=end,
            lat=lat,
            lon=lon,
            radius_km=radius_km,
            bbox=bbox_tuple,
        )
    except NasaTempoInvalidQuery as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except EarthdataAuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except NasaTempoServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    results = _normalize_measurements(
        payload, fallback_parameter=parameter, limit=limit
    )

    return {"source": "nasa-tempo", "results": results}
