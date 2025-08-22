import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { useEffect } from "react";

export default function MapView() {
  useEffect(() => {
    const map = new maplibregl.Map({
      container: "map", 
      style: "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json", // 🌍 estilo con calles
      center: [-64.1888, -31.4201], // Córdoba
      zoom: 9,
    });

    new maplibregl.Marker().setLngLat([-64.1888, -31.4201]).addTo(map);

    return () => map.remove();
  }, []);

  return (
    <div id="map" style={{ width: "100%", height: "80vh" }} />
  );
}
