// src/lib/api.js
import { DEFAULT_POLLUTANT } from "../constants/pollutants";

// Conversión molecules/cm^2 -> mol/m^2
const AVOGADRO = 6.02214076e23;
const MOL_PER_M2_PER_MOLEC_CM2 = 1e4 / AVOGADRO; // ≈ 1.66054e-20

function normalizeValueAndUnit(parameter, value, unit) {
  const p = String(parameter || "").toLowerCase();
  if (unit === "molecules/cm^2" && (p === "no2" || p === "so2" || p === "hcho")) {
    return { value: value * MOL_PER_M2_PER_MOLEC_CM2, unit: "mol/m²" };
  }
  return { value, unit }; // O3 en DU ya está bien
}

// Path del router (configurable via VITE_TEMPO_PATH, default: "tempo")
const TEMPO_PATH = (import.meta.env.VITE_TEMPO_PATH ?? "tempo").trim() || "tempo";

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

// ── Helpers ──────────────────────────────────────────────────────────────────
export function bboxFromMap(map) {
  const b = map.getBounds();
  const raw = [b.getWest(), b.getSouth(), b.getEast(), b.getNorth()];
  return raw.map((x) => +x.toFixed(3));
}

const toBackendParam = (p) => String(p || "").toLowerCase();

function toNumberSafe(v) {
  const n = Number.parseFloat(String(v).replace(",", "."));
  return Number.isFinite(n) ? n : null;
}

// Cache simple
const cache = new Map();
const TTL_MS = 120_000; // 2 minutos

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
      const valNum = toNumberSafe(value);
      const { value: convVal, unit: convUnit } =
        normalizeValueAndUnit(parameter, valNum, unit);

      return {
        type: "Feature",
        geometry: { type: "Point", coordinates: [Number(lon), Number(lat)] },
        properties: {
          parameter: toBackendParam(parameter),
          value: convVal,
          unit: convUnit || "",
          datetime: datetime || "",
        },
      };
    });
  return { type: "FeatureCollection", features };
}

function passthroughOrTempoToGeoJSON(data) {
  if (data && Array.isArray(data.features)) {
    return { type: "FeatureCollection", features: data.features };
  }
  return tempoResultsToGeoJSON(data);
}

// ── Carga por vista (usa lat/lon/radius) ─────────────────────────────────────
export async function fetchMeasurements({ bbox, pollutant, signal }) {
  if (import.meta.env.VITE_DISABLE_TEMPO === "1") {
    return { type: "FeatureCollection", features: [] };
  }

  const [w, s, e, n] = bbox;
  const lat = (s + n) / 2;
  const lon = (w + e) / 2;
  const latKm = 111_000;
  const lonKm = 111_000 * Math.cos((lat * Math.PI) / 180);
  const rx = (Math.abs(e - w) * lonKm) / 2;
  const ry = (Math.abs(n - s) * latKm) / 2;
  const radius = Math.min(Math.hypot(rx, ry), 30_000); // máx 30 km

  const url = apiUrl(`${TEMPO_PATH}/normalized`);
  url.searchParams.set("lat", lat.toFixed(5));
  url.searchParams.set("lon", lon.toFixed(5));
  url.searchParams.set("radius", String(Math.round(radius)));
  url.searchParams.set("limit", "200");
  url.searchParams.set("parameter", toBackendParam(pollutant));
  // filtros que alivian al back y mejoran mapa
  url.searchParams.set("nonneg", "true");
  url.searchParams.set("dropzero", "true");
  url.searchParams.set("thin", "3");
  if (["no2", "hcho"].includes(toBackendParam(pollutant))) {
    url.searchParams.set("min", "1e15");
  }

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
export async function fetchAtPoint({ lat, lon, pollutant = DEFAULT_POLLUTANT, signal }) {
  if (import.meta.env.VITE_DISABLE_TEMPO === "1") {
    return null;
  }

  const url = apiUrl(`${TEMPO_PATH}/normalized`);
  url.searchParams.set("lat", String(lat.toFixed(5)));
  url.searchParams.set("lon", String(lon.toFixed(5)));
  url.searchParams.set("radius", "2000"); // ~2 km
  url.searchParams.set("limit", "12");
  url.searchParams.set("parameter", toBackendParam(pollutant));
  // mismos filtros
  url.searchParams.set("nonneg", "true");
  url.searchParams.set("dropzero", "true");
  url.searchParams.set("thin", "3");
  if (["no2", "hcho"].includes(toBackendParam(pollutant))) {
    url.searchParams.set("min", "1e15");
  }

  const res = await fetch(url, { signal });
  if (!res.ok) throw new Error(`API ${res.status}`);
  const data = await res.json();

  const fc = passthroughOrTempoToGeoJSON(data);
  const f0 = fc.features?.[0];
  return f0 ? { ...f0.properties } : null;
}
