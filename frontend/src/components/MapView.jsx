import { useLayoutEffect, useRef } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

export default function MapView() {
  const mapRef = useRef(null);
  const divRef = useRef(null);

  useLayoutEffect(() => {
    console.log("[MapView] useEffect enter", { div: !!divRef.current });

    // Esperá hasta que el div exista (caso StrictMode / timing)
    let raf;
    const waitForDiv = () => {
      if (!divRef.current) {
        raf = requestAnimationFrame(waitForDiv);
        return;
      }
      if (mapRef.current) return;

      console.log("[MapView] creando mapa…");
      const rasterStyle = {
        version: 8,
        sources: {
          osm: {
            type: "raster",
            tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
            tileSize: 256,
            attribution:
              '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>',
          },
        },
        layers: [{ id: "osm", type: "raster", source: "osm" }],
      };

      const map = new maplibregl.Map({
        container: divRef.current,
        style: rasterStyle,
        center: [-64.1888, -31.4201],
        zoom: 12,
        attributionControl: false,
      });

      // por si el layout aún no calculó altura:
      requestAnimationFrame(() => map.resize());

      map.on("load", () => console.log("[MapView] map load"));
      map.on("error", (e) => console.warn("[MapView] map error:", e?.error));

      mapRef.current = map;
    };

    waitForDiv();
    return () => {
      cancelAnimationFrame(raf);
      if (mapRef.current) mapRef.current.remove();
    };
  }, []);

  return (
    <div
      ref={divRef}
      style={{ height: "70vh", minHeight: 420, outline: "2px dashed #09f" }}
    />
  );
}
