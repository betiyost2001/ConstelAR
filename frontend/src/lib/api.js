// src/lib/api.js
import { API_TO_UI, DEFAULT_POLLUTANT, UI_TO_API } from "../constants/pollutants";

// Forzamos el path del router a "openaq" (evita que vaya a /tempo)
const TEMPO_PATH = "openaq";
console.log("[API] TEMPO_PATH =", TEMPO_PATH);

// Límites por defecto (usados por el Map)
export const NORTH_AMERICA_BOUNDS = { west: -168, south: 5, east: -52, north: 83 };

// Base configurable: absoluto (http...) o relativo (/api). Default: /api
const RAW_BASE = (import.meta.env.VITE_API_BASE || "/api").trim();

// Siempre construye una URL absoluta válida (evita "Invalid URL")
function apiUrl(pathname) {
  const absBase = RAW_BASE.startsWith("http")
    ? RAW_BASE
    : window.location.origin + (RAW_BASE.startsWith("/") ? RAW_BASE : `/${RAW_BASE}`);
  const base = absBase.endsWith("/") ? absBase : absBase + "/";
  return new URL(pathname, base);
}

// ── Alias UI ↔ API ───────────────────────────────────────────────────────────
const toApiParam = (p) => UI_TO_API[p] || p;
const toUiParam  = (p) => API_TO_UI[p] || p;

// ── Cache ────────────────────────────────────────────────────────────────────
const cache = new Map();
const TTL_MS = 30_000;
const cacheKey = ({ pollutant, bbox }) => `${pollutant}:${bbox.join(",")}`;
const setCache  = (k, v) => cache.set(k, { value: v, exp: Date.now() + TTL_MS });
const getCache  = (k) => {
  const it = cache.get(k);
  if (!it) return null;
  if (Date.now() > it.exp) { cache.delete(k); return null; }
  return it.value;
};

// ── Helpers ──────────────────────────────────────────────────────────────────
export function bboxFromMap(map) {
  const b = map.getBounds();
  const raw = [b.getWest(), b.getSouth(), b.getEast(), b.getNorth()];
  return raw.map((x) => +x.toFixed(3));
}

// Normaliza a número, tolera coma decimal "12,3"
function toNumberSafe(v) {
  const n = Number.parseFloat(String(v).replace(",", "."));
  return Number.isFinite(n) ? n : null;
}

// ── Carga por vista (usa lat/lon/radius porque tu backend aún no acepta bbox) ──
export async function fetchMeasurements({ bbox, pollutant, signal }) {
  // Centro y radio aproximado a partir del BBOX
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
  url.searchParams.set("parameter", toApiParam(pollutant));

  const key = cacheKey({ pollutant, bbox });
  const fromCache = getCache(key);
  if (fromCache) return fromCache;

  const res = await fetch(url, { signal });
  if (!res.ok) throw new Error(`API ${res.status}`);
  const data = await res.json();

  const features = normalizeFeatureCollection(data, { pollutant });
  const fc = { type: "FeatureCollection", features };

  setCache(key, fc);
  return fc;
}

// ── Consulta puntual (click) — también usa lat/lon/radius ────────────────────
export async function fetchAtPoint({ lat, lon, pollutant = DEFAULT_POLLUTANT, signal }) {
  const url = apiUrl(`${TEMPO_PATH}/normalized`);
  url.searchParams.set("lat", lat.toFixed(5));
  url.searchParams.set("lon", lon.toFixed(5));
  url.searchParams.set("radius", "2000"); // 2 km
  url.searchParams.set("limit", "20");
  url.searchParams.set("parameter", toApiParam(pollutant));

  const res = await fetch(url, { signal });
  if (!res.ok) throw new Error(`API ${res.status}`);
  const data = await res.json();

  const features = normalizeFeatureCollection(data, { pollutant });
  const match = features.find((f) => f.properties.parameter === pollutant);
  const picked = match || features[0] || null;

  return picked ? { ...picked.properties } : null;
}

// ── Normalización de respuestas ──────────────────────────────────────────────
function normalizeFeatureCollection(data, { pollutant }) {
  const raw = Array.isArray(data?.features)
    ? data.features
    : Array.isArray(data?.results)
      ? data.results
      : Array.isArray(data?.data)
        ? data.data
        : [];

  return raw
    .map((feature) => normalizeFeature(feature, pollutant))
    .filter(Boolean);
}

function normalizeFeature(feature, fallbackPollutant) {
  if (!feature) return null;

  // Si ya viene como Feature con geometry, usamos eso
  let geometry = ensurePointGeometry(feature);

  // Si es un objeto "plano" (lat/lon/parameter/value...), lo convertimos
  if (!geometry) {
    const lon = toNumberSafe(feature.lon ?? feature.longitude ?? feature.x);
    const lat = toNumberSafe(feature.lat ?? feature.latitude ?? feature.y);
    if (lat != null && lon != null) {
      geometry = { type: "Point", coordinates: [lon, lat] };
    } else {
      return null;
    }
  }

  const srcProps = feature.properties ?? feature;
  const parameterRaw =
    srcProps.parameter ??
    srcProps.pollutant ??
    srcProps.species ??
    srcProps.product ??
    fallbackPollutant;

  const valueRaw =
    srcProps.value ??
    srcProps.measurement ??
    srcProps.average ??
    srcProps.avg ??
    srcProps.mean ??
    null;

  const datetime =
    srcProps.datetime ??
    srcProps.timestamp ??
    srcProps.time ??
    srcProps.date ??
    null;

  const unit = srcProps.unit ?? srcProps.units ?? srcProps.unit_of_measurement ?? "";

  return {
    type: "Feature",
    geometry,
    properties: {
      parameter: toUiParam(parameterRaw),
      value: toNumberSafe(valueRaw),
      unit,
      datetime,
    },
  };
}

function ensurePointGeometry(feature) {
  const geom = feature?.geometry;
  if (geom?.type === "Point" && Array.isArray(geom.coordinates) && geom.coordinates.length >= 2) {
    const [lon, lat] = geom.coordinates;
    if (Number.isFinite(lon) && Number.isFinite(lat)) {
      return { type: "Point", coordinates: [lon, lat] };
    }
  }
  return null;
}
