import { useLayoutEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import {
  fetchMeasurements,
  bboxFromMap,
  fetchAtPoint,
  NORTH_AMERICA_BOUNDS,
} from "../lib/api";
import { colorExpression } from "../constants/aqi";
import {
  DEFAULT_POLLUTANT,
  getPollutantLabel,
  getPollutantUnit,
} from "../constants/pollutants";
import FloatingNotificationButton from "./FloatingNotificationButton";
import SubscriptionModal from "./SubscriptionModal";

function debounce(fn, ms) {
  let t;
  return (...args) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...args), ms);
  };
}

/**
 * Props:
 * - pollutant?: contaminante soportado por TEMPO
 * - fetcher?: ({bbox, pollutant, signal}) => GeoJSON
 * - center?: [lng, lat]
 * - zoom?: number
 */
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
}) {
  const mapRef = useRef(null);
  const divRef = useRef(null);
  const abortRef = useRef(null);
  const clickHandlerRef = useRef(null);
  const resizeObsRef = useRef(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

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
      const SEL_SOURCE = "selected-point";
      const SEL_LAYER = "selected-circle";

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
          });

          if (!map.getSource(SOURCE_ID)) {
            map.addSource(SOURCE_ID, { type: "geojson", data: geojson });
            map.addLayer({
              id: LAYER_ID,
              type: "circle",
              source: SOURCE_ID,
              paint: {
                "circle-color": colorExpression("value", pollutant),
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
            // visible por defecto
            +map.setLayoutProperty(LAYER_ID, "visibility", "visible");
          } else {
            map.getSource(SOURCE_ID).setData(geojson);
            map.setPaintProperty(
              LAYER_ID,
              "circle-color",
              colorExpression("value", pollutant)
            );
            map.setLayoutProperty(LAYER_ID, "visibility", "visible");
          }
        } catch (e) {
          if (e?.name !== "AbortError") console.error("AQ load error:", e);
        }
      }

      function ensureSelectionLayer() {
        if (!map.getSource(SEL_SOURCE)) {
          map.addSource(SEL_SOURCE, {
            type: "geojson",
            data: { type: "FeatureCollection", features: [] },
          });
          map.addLayer({
            id: SEL_LAYER,
            type: "circle",
            source: SEL_SOURCE,
            paint: {
              "circle-color": [
                "case",
                ["has", "value"],
                colorExpression("value", pollutant),
                "#666",
              ],
              "circle-radius": [
                "interpolate",
                ["linear"],
                ["zoom"],
                3,
                5,
                12,
                10,
              ],
              "circle-stroke-color": "#000",
              "circle-stroke-width": 2,
              "circle-opacity": 0.95,
            },
          });
        }

        if (clickHandlerRef.current) map.off("click", clickHandlerRef.current);

        const onClick = async (ev) => {
          const { lng, lat } = ev.lngLat;

          map.getSource(SEL_SOURCE).setData({
            type: "FeatureCollection",
            features: [
              {
                type: "Feature",
                geometry: { type: "Point", coordinates: [lng, lat] },
                properties: {},
              },
            ],
          });

          try {
            const m = await fetchAtPoint({ lat, lon: lng, pollutant });
            if (m) {
              const parameterId = m.parameter || pollutant;
              const val = toSafeNumber(m.value);
              const unit = m.unit || getPollutantUnit(parameterId);

              map.getSource(SEL_SOURCE).setData({
                type: "FeatureCollection",
                features: [
                  {
                    type: "Feature",
                    geometry: { type: "Point", coordinates: [lng, lat] },
                    properties: {
                      parameter: parameterId,
                      value: val,
                      unit,
                      datetime: m.datetime,
                    },
                  },
                ],
              });

              const label = getPollutantLabel(parameterId);
              const html = `
                <div style="font-family: 'Overpass', system-ui; padding:6px 4px; color:#fff;">
                  <div><b>${label}</b>: ${
                Number.isFinite(val) ? val.toFixed(3) : "-"
              } ${unit || ""}</div>
                  <div style="color:#B8C0DD; font-size:12px">${
                    m.datetime ?? ""
                  }</div>
                  <div style="color:#9AA3C0; font-size:11px">(${lat.toFixed(
                    5
                  )}, ${lng.toFixed(5)})</div>
                </div>
              `;
              new maplibregl.Popup({ closeButton: true, maxWidth: "260px" })
                .setLngLat([lng, lat])
                .setHTML(html)
                .addTo(map);
            }
          } catch (err) {
            console.error("Point query error:", err);
          }
        };

        clickHandlerRef.current = onClick;
        map.on("click", onClick);
        map.getCanvas().style.cursor = "crosshair";
      }

      const debounced = debounce(loadForCurrentView, 400);
      const boot = () => {
        ensureSelectionLayer();
        loadForCurrentView();
      };
      if (map.isStyleLoaded()) boot();
      else map.once("idle", boot);
      map.on("moveend", debounced);

      resizeObsRef.current = new ResizeObserver(() => map.resize());
      resizeObsRef.current.observe(el);
    };

    init();
    return () => {
      cancelAnimationFrame(raf);
      abortRef.current?.abort();
      const map = mapRef.current;
      if (map && clickHandlerRef.current)
        map.off("click", clickHandlerRef.current);
      try {
        resizeObsRef.current?.disconnect();
      } catch (error) {
        console.error("No se que :", error);
      }
      mapRef.current?.remove();
      mapRef.current = null;

      if (divRef.current) delete divRef.current.__maplibre_initialized;
    };
  }, [pollutant, fetcher, center, zoom]);

  // Si cambia el contaminante, refrescar color del punto seleccionado
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
    <>
      <div
        ref={divRef}
        className="map-container spaceapps-bg"
        aria-label="Vista de mapa con mediciones de calidad del aire"
        role="region"
      />

      {/* Botón flotante de notificaciones */}
      <FloatingNotificationButton onOpenModal={() => setIsModalOpen(true)} />

      {/* Modal de suscripción */}
      <SubscriptionModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
    </>
  );
}

function toSafeNumber(value) {
  if (value == null) return null;
  const parsed = Number.parseFloat(String(value).replace(",", "."));
  return Number.isFinite(parsed) ? parsed : null;
}
