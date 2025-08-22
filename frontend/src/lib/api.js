const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

// POR CIUDAD (llama a tu backend)
export async function getOpenAQLatestByCity(city, limit = 5) {
  const url = `${BASE}/openaq/latest?city=${encodeURIComponent(city)}&limit=${limit}`;
  const r = await fetch(url);
  if (!r.ok) throw new Error(`Backend ${r.status}`);
  return r.json();
}

// POR COORDENADAS (recomendada)
export async function getOpenAQLatestByCoords(lat, lon, radius = 100000, limit = 10) {
  const url = `${BASE}/openaq/latest?lat=${lat}&lon=${lon}&radius=${radius}&limit=${limit}`;
  const r = await fetch(url);
  if (!r.ok) throw new Error(`Backend ${r.status}`);
  return r.json();
}
