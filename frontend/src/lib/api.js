// src/lib/api.js
const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000/api";

// ── Alias UI → API y API → UI ────────────────────────────────────────────────
const UI_TO_API = {
  pm25: "pm2_5",
  o3: "ozone",
  no2: "nitrogen_dioxide",
  so2: "sulphur_dioxide",
  co:  "carbon_monoxide",
  nh3: "ammonia",
};
const API_TO_UI = Object.fromEntries(Object.entries(UI_TO_API).map(([k,v]) => [v,k]));
const toApiParam  = (p) => UI_TO_API[p] || p;
const toUiParam   = (p) => API_TO_UI[p] || p;

// ── Cache ────────────────────────────────────────────────────────────────────
const cache = new Map();
const TTL_MS = 30_000;
const cacheKey = ({ pollutant, bbox }) => `${pollutant}:${bbox.join(",")}`;
const setCache = (k, v) => cache.set(k, { value: v, exp: Date.now() + TTL_MS });
const getCache = (k) => { const it = cache.get(k); if (!it) return null; if (Date.now()>it.exp){cache.delete(k);return null;} return it.value; };

// ── Helpers ──────────────────────────────────────────────────────────────────
export function bboxFromMap(map) {
  const b = map.getBounds();
  const raw = [b.getWest(), b.getSouth(), b.getEast(), b.getNorth()];
  return raw.map(x => +x.toFixed(3));
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

  const url = new URL(`${API_BASE}/openaq/normalized`);
  url.searchParams.set("lat", lat.toFixed(5));
  url.searchParams.set("lon", lon.toFixed(5));
  url.searchParams.set("radius", Math.round(radiusMeters));
  url.searchParams.set("limit", "200");
  url.searchParams.set("parameter", toApiParam(pollutant)); // <-- alias

  const key = cacheKey({ pollutant, bbox });
  const fromCache = getCache(key);
  if (fromCache) return fromCache;

  const res = await fetch(url, { signal });
  if (!res.ok) throw new Error(`API ${res.status}`);
  const data = await res.json();

  // Normalizamos a GeoJSON con el nombre UI
  const fc = {
    type: "FeatureCollection",
    features: (data.results || []).map(r => ({
      type: "Feature",
      geometry: { type: "Point", coordinates: [r.lon, r.lat] },
      properties: {
  parameter: m.parameter || pollutant,
  value: Number(m.value),        // << clave: aseguramos número
  unit: m.unit,
  datetime: m.datetime,
},

    }))
  };

  setCache(key, fc);
  return fc;
}

// ── Consulta puntual (click) ────────────────────────────────────────────────
export async function fetchAtPoint({ lat, lon, pollutant = "pm25", signal }) {
  const url = new URL(`${API_BASE}/openaq/normalized`);
  url.searchParams.set("lat", lat.toFixed(5));
  url.searchParams.set("lon", lon.toFixed(5));
  url.searchParams.set("radius", "2000");
  url.searchParams.set("limit", "20");
  url.searchParams.set("parameter", toApiParam(pollutant)); // <-- alias correcto

  const res = await fetch(url, { signal });
  if (!res.ok) throw new Error(`API ${res.status}`);
  const data = await res.json();

  const list = Array.isArray(data?.results) ? data.results : [];
  // comparamos usando el nombre UI
  const byPollutant = list
    .map(r => ({ ...r, parameter: toUiParam(r.parameter) }))
    .filter(r => r.parameter === pollutant);

  const picked = byPollutant[0] || (list[0] && { ...list[0], parameter: toUiParam(list[0].parameter) }) || null;
  return picked;
}
