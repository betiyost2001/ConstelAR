import { useEffect, useRef } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

export default function MapView() {
  const mapRef = useRef(null);

  useEffect(() => {
    if (!mapRef.current) return;
    const map = new maplibregl.Map({
      container: mapRef.current,
      style: "https://demotiles.maplibre.org/style.json",
      center: [-64.1888, -31.4201], // Córdoba
      zoom: 11
    });
    return () => map.remove();
  }, []);

  return <div ref={mapRef} style={{ height: "calc(100vh - 64px)" }} />;
}
