import { useLayoutEffect, useRef } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { fetchMeasurements, bboxFromMap, fetchAtPoint } from "../lib/api";
import { colorExpression } from "../constants/aqi";

function debounce(fn, ms) {
  let t;
  return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
}

export default function MapView({ pollutant = "pm25", fetcher = fetchMeasurements }) {
  const mapRef = useRef(null);
  const divRef = useRef(null);
  const abortRef = useRef(null);
  const clickHandlerRef = useRef(null);

  useLayoutEffect(() => {
    let raf;

    const init = () => {
      if (!divRef.current) { raf = requestAnimationFrame(init); return; }
      if (mapRef.current) return;

      const rasterStyle = {
        version: 8,
        sources: {
          osm: {
            type: "raster",
            tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
            tileSize: 256,
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>',
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
      mapRef.current = map;

      map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), "top-right");
      map.addControl(new maplibregl.AttributionControl({ compact: true }), "bottom-right");

      const SOURCE_ID  = "aq-points";
      const LAYER_ID   = "aq-circles";
      const SEL_SOURCE = "selected-point";
      const SEL_LAYER  = "selected-circle";

      async function loadForCurrentView() {
        abortRef.current?.abort();
        const controller = new AbortController();
        abortRef.current = controller;

        try {
          const bbox = bboxFromMap(map);
          const geojson = await fetcher({ bbox, pollutant, signal: controller.signal });

          if (!map.getSource(SOURCE_ID)) {
            map.addSource(SOURCE_ID, { type: "geojson", data: geojson });
            map.addLayer({
              id: LAYER_ID,
              type: "circle",
              source: SOURCE_ID,
              paint: {
                "circle-color": colorExpression("value", pollutant),
                "circle-radius": ["interpolate", ["linear"], ["zoom"], 3, 3, 8, 6, 12, 9],
                "circle-opacity": 0.85,
              },
            });
            // 🔕 Ocultamos el layer de fondo para que no se vea el punto "naranja"
            map.setLayoutProperty(LAYER_ID, "visibility", "none");
          } else {
            map.getSource(SOURCE_ID).setData(geojson);
            map.setPaintProperty(LAYER_ID, "circle-color", colorExpression("value", pollutant));
            // mantenerlo oculto siempre
            map.setLayoutProperty(LAYER_ID, "visibility", "none");
          }
        } catch (e) {
          if (e.name !== "AbortError") console.error("AQ load error:", e);
        }
      }

      // Capa de selección (única interacción de click)
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
              "circle-color": ["case", ["has", "value"], colorExpression("value", pollutant), "#666"],
              "circle-radius": ["interpolate", ["linear"], ["zoom"], 3, 5, 12, 10],
              "circle-stroke-color": "#000",
              "circle-stroke-width": 2,
              "circle-opacity": 0.95,
            },
          });
        }

        // Evitar listeners duplicados en HMR
        if (clickHandlerRef.current) map.off("click", clickHandlerRef.current);

        const onClick = async (ev) => {
          const { lng, lat } = ev.lngLat;

          // Pintamos inmediatamente el círculo gris
          map.getSource(SEL_SOURCE).setData({
            type: "FeatureCollection",
            features: [{
              type: "Feature",
              geometry: { type: "Point", coordinates: [lng, lat] },
              properties: {},
            }],
          });

          try {
            const m = await fetchAtPoint({ lat, lon: lng, pollutant });
            if (m) {
              map.getSource(SEL_SOURCE).setData({
                type: "FeatureCollection",
                features: [{
                  type: "Feature",
                  geometry: { type: "Point", coordinates: [lng, lat] },
                  properties: {
                    parameter: m.parameter || pollutant,
                    value: m.value,
                    unit: m.unit,
                    datetime: m.datetime,
                  },
                }],
              });

              new maplibregl.Popup({ closeButton: true })
                .setLngLat([lng, lat])
                .setHTML(`
                  <div style="font-family: system-ui; padding:4px 2px">
                    <div><b>${m.parameter || pollutant}</b>: ${Number(m.value).toFixed(1)} ${m.unit || ""}</div>
                    <div style="color:#666; font-size:12px">${m.datetime ?? ""}</div>
                    <div style="color:#777; font-size:11px">(${lat.toFixed(5)}, ${lng.toFixed(5)})</div>
                  </div>
                `)
                .addTo(map);
            }
          } catch (err) {
            console.error("Point query error:", err);
          }
        };

        clickHandlerRef.current = onClick;
        map.on("click", onClick);
      }

      const debounced = debounce(loadForCurrentView, 400);

      const boot = () => { ensureSelectionLayer(); loadForCurrentView(); };
      if (map.isStyleLoaded()) boot();
      else map.once("idle", boot);

      map.on("moveend", debounced);
    };

    init();
    return () => {
      cancelAnimationFrame(raf);
      abortRef.current?.abort();
      const map = mapRef.current;
      if (map && clickHandlerRef.current) map.off("click", clickHandlerRef.current);
      mapRef.current?.remove();
      mapRef.current = null;
    };
  }, [pollutant, fetcher]);

  // Si cambia el contaminante, refrescamos color del punto seleccionado
  useLayoutEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    if (map.getLayer("selected-circle")) {
      map.setPaintProperty(
        "selected-circle",
        "circle-color",
        ["case", ["has", "value"], colorExpression("value", pollutant), "#666"]
      );
    }
  }, [pollutant]);

  return <div ref={divRef} className="map-container" />;
}
