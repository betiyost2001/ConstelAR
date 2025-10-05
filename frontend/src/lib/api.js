// src/lib/api.js
import { DEFAULT_POLLUTANT } from "../constants/pollutants";

// Path del router (configurable via VITE_TEMPO_PATH, default: "tempo")
const TEMPO_PATH =
  (import.meta.env.VITE_TEMPO_PATH ?? "tempo").trim() || "tempo";

// Límites por defecto (usados por el Map)
export const NORTH_AMERICA_BOUNDS = {
  west: -168,
  south: 5,
  east: -52,
  north: 83,
};

// Base configurable: absoluto (http...) o relativo (/api). Default: /api
const RAW_BASE = (import.meta.env.VITE_API_BASE || "/api").trim();

// Siempre construye una URL absoluta válida (evita "Invalid URL")
function apiUrl(pathname) {
  const absBase = RAW_BASE.startsWith("http")
    ? RAW_BASE
    : window.location.origin +
      (RAW_BASE.startsWith("/") ? RAW_BASE : `/${RAW_BASE}`);
  const base = absBase.endsWith("/") ? absBase : absBase + "/";
  return new URL(pathname, base);
}

// ── Helpers ──────────────────────────────────────────────────────────────────
export function bboxFromMap(map) {
  const b = map.getBounds();
  const raw = [b.getWest(), b.getSouth(), b.getEast(), b.getNorth()];
  return raw.map((x) => +x.toFixed(3));
}

// Minúsculas para backend (no2, o3, so2, hcho)
const toBackendParam = (p) => String(p || "").toLowerCase();

// Normaliza a número, tolera coma decimal "12,3"
function toNumberSafe(v) {
  const n = Number.parseFloat(String(v).replace(",", "."));
  return Number.isFinite(n) ? n : null;
}

// Cache simple
const cache = new Map();
const TTL_MS = 30_000;
const cacheKey = ({ pollutant, bbox }) => `${pollutant}:${bbox.join(",")}`;
const setCache = (k, v) => cache.set(k, { value: v, exp: Date.now() + TTL_MS });
const getCache = (k) => {
  const it = cache.get(k);
  if (!it) return null;
  if (Date.now() > it.exp) {
    cache.delete(k);
    return null;
  }
  return it.value;
};

// Convierte payload del backend TEMPO {results:[[lat,lon,param,value,unit,datetime],...]} a GeoJSON
function tempoResultsToGeoJSON(data) {
  const rows = Array.isArray(data?.results) ? data.results : [];
  const features = rows
    .filter((r) => Array.isArray(r) && r.length >= 6)
    .map((r) => {
      const [lat, lon, parameter, value, unit, datetime] = r;
      const val = toNumberSafe(value);
      return {
        type: "Feature",
        geometry: { type: "Point", coordinates: [Number(lon), Number(lat)] },
        properties: {
          parameter: toBackendParam(parameter),
          value: val,
          unit: unit || "",
          datetime: datetime || "",
        },
      };
    });
  return { type: "FeatureCollection", features };
}

// Fallback: si el backend algún día devuelve GeoJSON nativo
function passthroughOrTempoToGeoJSON(data) {
  if (data && Array.isArray(data.features)) {
    return { type: "FeatureCollection", features: data.features };
  }
  return tempoResultsToGeoJSON(data);
}

// ── Carga por vista (usa lat/lon/radius) ─────────────────────────────────────
export async function fetchMeasurements({ bbox, pollutant, signal }) {
  // Modo temporal: deshabilitar llamadas a /tempo en desarrollo
  if (import.meta.env.VITE_DISABLE_TEMPO === "1") {
    return { type: "FeatureCollection", features: [] };
  }

  // Centro y radio aprox a partir del BBOX
  const [w, s, e, n] = bbox;
  const lat = (s + n) / 2;
  const lon = (w + e) / 2;
  const latKm = 111_000;
  const lonKm = 111_000 * Math.cos((lat * Math.PI) / 180);
  const rx = (Math.abs(e - w) * lonKm) / 2;
  const ry = (Math.abs(n - s) * latKm) / 2;
  const radius = Math.min(Math.hypot(rx, ry), 50_000); // máx. 50 km

  const url = apiUrl(`${TEMPO_PATH}/normalized`);
  url.searchParams.set("lat", lat.toFixed(5));
  url.searchParams.set("lon", lon.toFixed(5));
  url.searchParams.set("radius", String(Math.round(radius)));
  url.searchParams.set("limit", "200");
  url.searchParams.set("parameter", toBackendParam(pollutant));

  const key = cacheKey({ pollutant, bbox });
  const fromCache = getCache(key);
  if (fromCache) return fromCache;

  const res = await fetch(url, { signal });
  if (!res.ok) throw new Error(`API ${res.status}`);
  const data = await res.json();

  const fc = passthroughOrTempoToGeoJSON(data);
  setCache(key, fc);
  return fc;
}

// ── Consulta puntual (click) ─────────────────────────────────────────────────
export async function fetchAtPoint({
  lat,
  lon,
  pollutant = DEFAULT_POLLUTANT,
  signal,
}) {
  // Modo temporal: deshabilitar llamadas a /tempo en desarrollo
  if (import.meta.env.VITE_DISABLE_TEMPO === "1") {
    return null;
  }

  const url = apiUrl(`${TEMPO_PATH}/normalized`);
  url.searchParams.set("lat", String(lat.toFixed(5)));
  url.searchParams.set("lon", String(lon.toFixed(5)));
  url.searchParams.set("radius", "2000"); // ~2 km
  url.searchParams.set("limit", "20");
  url.searchParams.set("parameter", toBackendParam(pollutant));

  const res = await fetch(url, { signal });
  if (!res.ok) throw new Error(`API ${res.status}`);
  const data = await res.json();

  const fc = passthroughOrTempoToGeoJSON(data);
  const f0 = fc.features?.[0];
  return f0 ? { ...f0.properties } : null;
}
