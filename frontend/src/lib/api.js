// src/lib/api.js

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
const UI_TO_API = {
  pm25: "pm2_5",
  o3: "ozone",
  no2: "nitrogen_dioxide",
  so2: "sulphur_dioxide",
  co: "carbon_monoxide",
  nh3: "ammonia",
};
const API_TO_UI = Object.fromEntries(Object.entries(UI_TO_API).map(([k, v]) => [v, k]));
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
  const [w, s, e, n] = bbox;
  const lat = (s + n) / 2;
  const lon = (w + e) / 2;
  const radiusMeters = Math.min(
    Math.hypot((e - w) * 111_000 * Math.cos((lat * Math.PI) / 180), (n - s) * 111_000) / 2,
    50_000
  );

  const url = apiUrl("openaq/normalized");
  url.searchParams.set("lat", lat.toFixed(5));
  url.searchParams.set("lon", lon.toFixed(5));
  url.searchParams.set("radius", String(Math.round(radiusMeters)));
  url.searchParams.set("limit", "200");
  url.searchParams.set("parameter", toApiParam(pollutant));

  const key = cacheKey({ pollutant, bbox });
  const fromCache = getCache(key);
  if (fromCache) return fromCache;

  const res = await fetch(url, { signal });
  if (!res.ok) throw new Error(`API ${res.status}`);
  const data = await res.json();

  // GeoJSON normalizado (parámetro en nombre UI y value numérico)
  const fc = {
    type: "FeatureCollection",
    features: (data.results || []).map((r) => ({
      type: "Feature",
      // Ajustá si tu API usa otras keys: longitude/latitude
      geometry: { type: "Point", coordinates: [r.lon, r.lat] },
      properties: {
        parameter: toUiParam(r.parameter),
        value: toNumberSafe(r.value),
        unit: r.unit,
        datetime: r.datetime,
      },
    })),
  };

  setCache(key, fc);
  return fc;
}

// ── Consulta puntual (click) ────────────────────────────────────────────────
export async function fetchAtPoint({ lat, lon, pollutant = "pm25", signal }) {
  const url = apiUrl("openaq/normalized");
  url.searchParams.set("lat", lat.toFixed(5));
  url.searchParams.set("lon", lon.toFixed(5));
  url.searchParams.set("radius", "2000");
  url.searchParams.set("limit", "20");
  url.searchParams.set("parameter", toApiParam(pollutant));

  const res = await fetch(url, { signal });
  if (!res.ok) throw new Error(`API ${res.status}`);
  const data = await res.json();

  const list = Array.isArray(data?.results) ? data.results : [];
  const byPollutant = list
    .map((r) => ({ ...r, parameter: toUiParam(r.parameter) }))
    .filter((r) => r.parameter === pollutant);

  const pickedRaw =
    byPollutant[0] ||
    (list[0] && { ...list[0], parameter: toUiParam(list[0].parameter) }) ||
    null;

  return pickedRaw ? { ...pickedRaw, value: toNumberSafe(pickedRaw.value) } : null;
}
