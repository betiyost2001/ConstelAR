import { useLayoutEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import MapboxDraw from "@mapbox/mapbox-gl-draw";
import "@mapbox/mapbox-gl-draw/dist/mapbox-gl-draw.css";
import { toast } from "react-toastify";

import {
  fetchMeasurements,
  bboxFromMap,
  NORTH_AMERICA_BOUNDS,
} from "../lib/api";
import { colorExpression } from "../constants/aqi";
import { DEFAULT_POLLUTANT } from "../constants/pollutants";
import FloatingNotificationButton from "./FloatingNotificationButton";
import SubscriptionModal from "./SubscriptionModal";

// util: debounce simple
function debounce(fn, ms) {
  let t;
  return (...args) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...args), ms);
  };
}

const DEFAULT_CENTER = [-99, 37];
const DEFAULT_ZOOM = 3.5;
const MAX_BOUNDS = [
  [NORTH_AMERICA_BOUNDS.west, NORTH_AMERICA_BOUNDS.south],
  [NORTH_AMERICA_BOUNDS.east, NORTH_AMERICA_BOUNDS.north],
];

export default function MapView({
  pollutant = DEFAULT_POLLUTANT,
  fetcher = fetchMeasurements,
  center = DEFAULT_CENTER,
  zoom = DEFAULT_ZOOM,
  selectedBbox,
  onBboxChange,
}) {
  const mapRef = useRef(null);
  const divRef = useRef(null);
  const abortRef = useRef(null);
  const resizeObsRef = useRef(null);
  const drawRef = useRef(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Mapa y capas
  useLayoutEffect(() => {
    let raf;

    const init = () => {
      const el = divRef.current;
      if (!el) {
        raf = requestAnimationFrame(init);
        return;
      }
      if (mapRef.current || el.__maplibre_initialized) return;
      el.__maplibre_initialized = true;

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
        container: el,
        style: rasterStyle,
        center,
        zoom,
        maxBounds: MAX_BOUNDS,
        attributionControl: false,
        pixelRatio: Math.max(1, Math.min(window.devicePixelRatio || 1, 2)),
        failIfMajorPerformanceCaveat: false,
      });
      mapRef.current = map;

      map.addControl(
        new maplibregl.NavigationControl({ visualizePitch: true }),
        "top-right"
      );
      map.addControl(
        new maplibregl.AttributionControl({ compact: true }),
        "bottom-right"
      );

      const SOURCE_ID = "aq-points";
      const LAYER_ID = "aq-circles";

      async function loadForCurrentView() {
        abortRef.current?.abort();
        const controller = new AbortController();
        abortRef.current = controller;

        try {
          const bbox = bboxFromMap(map);
          const geojson = await fetcher({
            bbox,
            pollutant,
            signal: controller.signal,
            selectedBbox,
          });

          if (!map.getSource(SOURCE_ID)) {
            map.addSource(SOURCE_ID, { type: "geojson", data: geojson });
            map.addLayer({
              id: LAYER_ID,
              type: "circle",
              source: SOURCE_ID,
              paint: {
                // Si no hay 'value', se pinta gris
                "circle-color": [
                  "case",
                  ["has", "value"],
                  colorExpression("value", pollutant),
                  "#CCCCCC",
                ],
                "circle-radius": [
                  "interpolate",
                  ["linear"],
                  ["zoom"],
                  3,
                  3,
                  8,
                  6,
                  12,
                  9,
                ],
                "circle-opacity": 0.85,
              },
            });
            map.setLayoutProperty(LAYER_ID, "visibility", "visible");
          } else {
            map.getSource(SOURCE_ID).setData(geojson);
            map.setPaintProperty(LAYER_ID, "circle-color", [
              "case",
              ["has", "value"],
              colorExpression("value", pollutant),
              "#CCCCCC",
            ]);
            map.setLayoutProperty(LAYER_ID, "visibility", "visible");
          }
        } catch (e) {
          if (e?.name !== "AbortError") {
            console.error("AQ load error:", e);
            toast.error("Error loading air quality data. Please try again.");
          }
        }
      }

      map.getCanvas().style.cursor = "default";

      const debounced = debounce(loadForCurrentView, 400);
      const boot = () => loadForCurrentView();

      if (map.isStyleLoaded()) boot();
      else map.once("load", boot);

      // Setup draw after map is loaded
      map.once("load", () => {
        const draw = new MapboxDraw({
          displayControlsDefault: true,
          controls: {
            polygon: true,
            trash: true,
          },
        });
        map.addControl(draw, "top-left");
        draw.changeMode("draw_polygon");
        drawRef.current = draw;

        map.on("draw.create", (e) => {
          const feature = e.features[0];
          if (feature.geometry.type === "Polygon") {
            const coords = feature.geometry.coordinates[0];
            const lons = coords.map((c) => c[0]);
            const lats = coords.map((c) => c[1]);
            const bbox = [
              Math.min(...lons),
              Math.min(...lats),
              Math.max(...lons),
              Math.max(...lats),
            ];
            onBboxChange(bbox);
            draw.changeMode("simple_select");
          }
        });
      });

      map.on("moveend", debounced);

      resizeObsRef.current = new ResizeObserver(() => map.resize());
      resizeObsRef.current.observe(el);
    };

    init();

    return () => {
      if (raf) cancelAnimationFrame(raf);
      abortRef.current?.abort();

      try {
        resizeObsRef.current?.disconnect();
      } catch (error) {
        console.error("Error al desconectar ResizeObserver:", error);
      }

      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }

      if (divRef.current) delete divRef.current.__maplibre_initialized;
    };
  }, [pollutant, fetcher, center, zoom, selectedBbox]);

  // Actualiza el color de la capa seleccionada si cambia el contaminante
  useLayoutEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    if (map.getLayer("selected-circle")) {
      map.setPaintProperty("selected-circle", "circle-color", [
        "case",
        ["has", "value"],
        colorExpression("value", pollutant),
        "#666",
      ]);
    }
  }, [pollutant]);

  return (
    <div style={{ height: "100%", width: "100%", position: "relative" }}>
      <div
        ref={divRef}
        className="map-container"
        style={{ height: "100%", width: "100%", background: "none" }}
        aria-label="Vista de mapa con mediciones de calidad del aire"
        role="region"
      />

      <FloatingNotificationButton onOpenModal={() => setIsModalOpen(true)} />

      <SubscriptionModal
        className="floating-btn"
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
    </div>
  );
}
