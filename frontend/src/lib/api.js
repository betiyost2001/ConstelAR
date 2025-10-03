// src/lib/api.js
import { API_TO_UI, DEFAULT_POLLUTANT, UI_TO_API } from "../constants/pollutants";

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

// ── Carga por vista ──────────────────────────────────────────────────────────
export async function fetchMeasurements({ bbox, pollutant, signal }) {
  const url = apiUrl("tempo/measurements");
  url.searchParams.set("bbox", bbox.map((x) => x.toFixed(3)).join(","));
  url.searchParams.set("parameter", toApiParam(pollutant));
  url.searchParams.set("limit", "500");

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

// ── Consulta puntual (click) ────────────────────────────────────────────────
export async function fetchAtPoint({ lat, lon, pollutant = DEFAULT_POLLUTANT, signal }) {
  const delta = 0.15; // ~15 km de radio alrededor del punto
  const bbox = [
    lon - delta,
    lat - delta,
    lon + delta,
    lat + delta,
  ];

  const url = apiUrl("tempo/measurements");
  url.searchParams.set("bbox", bbox.map((x) => x.toFixed(3)).join(","));
  url.searchParams.set("parameter", toApiParam(pollutant));
  url.searchParams.set("limit", "20");

  const res = await fetch(url, { signal });
  if (!res.ok) throw new Error(`API ${res.status}`);
  const data = await res.json();

  const features = normalizeFeatureCollection(data, { pollutant });
  const match = features.find((f) => f.properties.parameter === pollutant);
  const picked = match || features[0] || null;

  return picked ? { ...picked.properties } : null;
}

function normalizeFeatureCollection(data, { pollutant }) {
  const rawFeatures = Array.isArray(data?.features)
    ? data.features
    : Array.isArray(data?.results)
      ? data.results
      : Array.isArray(data?.data)
        ? data.data
        : [];

function ensurePointGeometry(feature) {
  const geom = feature.geometry;
  if (geom?.type === "Point" && Array.isArray(geom.coordinates) && geom.coordinates.length >= 2) {
    const [lon, lat] = geom.coordinates;
    if (Number.isFinite(lon) && Number.isFinite(lat)) {
      return { type: "Point", coordinates: [lon, lat] };
    }
  }

  const src = feature.properties ?? feature;
  const lon = toNumberSafe(src.lon ?? src.longitude ?? src.x ?? feature.lon ?? feature.longitude);
  const lat = toNumberSafe(src.lat ?? src.latitude ?? src.y ?? feature.lat ?? feature.latitude);
  if (lat == null || lon == null) return null;

  return { type: "Point", coordinates: [lon, lat] };
}}
