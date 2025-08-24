// frontend/src/lib/api.js
const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function getNormalized({ lat, lon, limit = 50, radius = 100000 }) {
  const qs = new URLSearchParams({
    lat: String(lat),
    lon: String(lon),
    radius: String(radius),
    limit: String(limit),
  }).toString();

  const url = `${BASE}/openaq/normalized?${qs}`;
  const res = await fetch(url, { credentials: "include" });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status} ${res.statusText} - ${text}`);
  }
  return res.json(); // { source, results }
}
