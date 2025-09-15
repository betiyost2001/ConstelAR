import {
  useLayoutEffect,
  useRef,
  useState,
  forwardRef,
  useImperativeHandle,
} from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import MapboxDraw from "@mapbox/mapbox-gl-draw";
import "@mapbox/mapbox-gl-draw/dist/mapbox-gl-draw.css";
import { PollutantType, SelectionMode, MapViewRef } from "../App";
import { bboxFromMap, fetchMeasurements } from "../lib/api";
import { colorExpression } from "../constants/aqi";
import {
  filterMockDataByPoint,
  filterMockDataByPolygon,
  generateMockData,
} from "../lib/mockData";

function debounce<T extends (...args: any[]) => void>(
  fn: T,
  ms: number
): (...args: Parameters<T>) => void {
  let t: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...args), ms);
  };
}

interface MapViewProps {
  pollutant?: PollutantType;
  fetcher?: (params: {
    bbox: number[];
    pollutant: PollutantType;
    signal: AbortSignal;
  }) => Promise<any>;
  center?: [number, number];
  zoom?: number;
  selectionMode?: SelectionMode;
  onClearSelection?: () => void;
  onResetView?: () => void;
}

interface SelectionData {
  type: "point" | "polygon";
  coordinates: number[] | number[][];
  data: any;
}

const MapView = forwardRef<MapViewRef, MapViewProps>(function MapView(
  {
    pollutant = "pm25",
    fetcher = fetchMeasurements,
    center = [-98.5795, 39.8283],
    zoom = 4,
    selectionMode = "point",
    onClearSelection,
    onResetView,
  },
  ref
): React.ReactElement {
  const mapRef = useRef<maplibregl.Map | null>(null);
  const divRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);
  const clickHandlerRef = useRef<
    ((ev: maplibregl.MapMouseEvent) => void) | null
  >(null);
  const resizeObsRef = useRef<ResizeObserver | null>(null);
  const drawRef = useRef<MapboxDraw | null>(null);
  const mockDataRef = useRef<any>(null);
  const [currentSelection, setCurrentSelection] =
    useState<SelectionData | null>(null);

  // Layer and source constants
  const SOURCE_ID = "aq-points";
  const LAYER_ID = "aq-circles";
  const SEL_SOURCE = "selected-point";
  const SEL_LAYER = "selected-circle";
  const HEATMAP_SOURCE = "heatmap-data";
  const HEATMAP_LAYER = "heatmap-layer";

  // Expose map functions to parent component
  useImperativeHandle(
    ref,
    () => ({
      _clearSelection: () => {
        const map = mapRef.current;
        const draw = drawRef.current;
        if (!map || !draw) return;

        // Clear selection marker
        const selSource = map.getSource(SEL_SOURCE) as maplibregl.GeoJSONSource;
        if (selSource) {
          selSource.setData({ type: "FeatureCollection", features: [] });
        }

        // Clear heatmap
        const heatmapSource = map.getSource(
          HEATMAP_SOURCE
        ) as maplibregl.GeoJSONSource;
        if (heatmapSource) {
          heatmapSource.setData({ type: "FeatureCollection", features: [] });
        }

        // Clear drawn features
        draw.deleteAll();

        setCurrentSelection(null);
      },
      _resetView: () => {
        const map = mapRef.current;
        if (!map) return;

        map.flyTo({
          center,
          zoom,
          essential: true,
        });
      },
    }),
    [center, zoom]
  );

  useLayoutEffect(() => {
    let raf: number;

    const init = () => {
      const el = divRef.current;
      if (!el) {
        raf = requestAnimationFrame(init);
        return;
      }
      if (mapRef.current || (el as any).__maplibre_initialized) return;
      (el as any).__maplibre_initialized = true;

      const rasterStyle = {
        version: 8 as const,
        sources: {
          osm: {
            type: "raster" as const,
            tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
            tileSize: 256,
            attribution:
              '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>',
          },
        },
        layers: [{ id: "osm", type: "raster" as const, source: "osm" }],
      };

      const map = new maplibregl.Map({
        container: el,
        style: rasterStyle,
        center,
        zoom,
        attributionControl: false,
        pixelRatio: Math.max(1, Math.min(window.devicePixelRatio || 1, 2)),
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

      // Initialize drawing tool
      const draw = new MapboxDraw({
        displayControlsDefault: false,
        controls: {
          polygon: true,
          trash: true,
        },
        defaultMode: "simple_select",
      });
      drawRef.current = draw;
      // TODO: arreglar types
      map.addControl(draw, "top-left");

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
            map.setLayoutProperty(LAYER_ID, "visibility", "none");
          } else {
            (map.getSource(SOURCE_ID) as maplibregl.GeoJSONSource)!.setData(
              geojson
            );
            map.setPaintProperty(
              LAYER_ID,
              "circle-color",
              colorExpression("value", pollutant)
            );
            map.setLayoutProperty(LAYER_ID, "visibility", "none");
          }
        } catch (e) {
          if ((e as Error)?.name !== "AbortError")
            console.error("AQ load error:", e);
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

        const onClick = async (ev: maplibregl.MapMouseEvent) => {
          if (selectionMode === "polygon") {
            // In polygon mode, don't handle clicks for point selection
            return;
          }

          const { lng, lat } = ev.lngLat;

          // Generate mock data for the current view if not already done
          if (!mockDataRef.current) {
            const bbox = bboxFromMap(map);
            mockDataRef.current = generateMockData(bbox, pollutant);
          }

          // Filter data by point (5km radius)
          const filteredData = filterMockDataByPoint(
            mockDataRef.current,
            [lng, lat],
            5
          );

          // Update heatmap with filtered data
          const heatmapSource = map.getSource(
            HEATMAP_SOURCE
          ) as maplibregl.GeoJSONSource;
          if (heatmapSource) {
            heatmapSource.setData(filteredData);
          }

          // Update selection marker
          (map.getSource(SEL_SOURCE) as maplibregl.GeoJSONSource)!.setData({
            type: "FeatureCollection",
            features: [
              {
                type: "Feature",
                geometry: { type: "Point", coordinates: [lng, lat] },
                properties: {},
              },
            ],
          });

          setCurrentSelection({
            type: "point",
            coordinates: [lng, lat],
            data: filteredData,
          });

          // Show popup with selection info
          const html = `
            <div style="font-family: 'Overpass', system-ui; padding:6px 4px; color:#fff;">
              <div><b>Point Selection</b></div>
              <div style="color:#B8C0DD; font-size:12px">${
                filteredData.features.length
              } data points within 5km</div>
              <div style="color:#9AA3C0; font-size:11px">(${lat.toFixed(
                5
              )}, ${lng.toFixed(5)})</div>
            </div>
          `;
          new maplibregl.Popup({ closeButton: true, maxWidth: "260px" })
            .setLngLat([lng, lat])
            .setHTML(html)
            .addTo(map);
        };

        clickHandlerRef.current = onClick;
        map.on("click", onClick);
        map.getCanvas().style.cursor =
          selectionMode === "point" ? "crosshair" : "default";

        // Handle drawing events
        map.on("draw.create", (e) => {
          if (selectionMode === "polygon") {
            const feature = e.features[0];
            if (feature && feature.geometry.type === "Polygon") {
              const coordinates = feature.geometry.coordinates[0];

              // Generate mock data if not already done
              if (!mockDataRef.current) {
                const bbox = bboxFromMap(map);
                mockDataRef.current = generateMockData(bbox, pollutant);
              }

              // Filter data by polygon
              const filteredData = filterMockDataByPolygon(
                mockDataRef.current,
                coordinates
              );

              // Update heatmap with filtered data
              const heatmapSource = map.getSource(
                HEATMAP_SOURCE
              ) as maplibregl.GeoJSONSource;
              if (heatmapSource) {
                heatmapSource.setData(filteredData);
              }

              setCurrentSelection({
                type: "polygon",
                coordinates: coordinates,
                data: filteredData,
              });

              // Show popup with selection info
              const center = coordinates
                .reduce(
                  (acc: number[], coord: number[]) => [
                    acc[0] + coord[0],
                    acc[1] + coord[1],
                  ],
                  [0, 0]
                )
                .map((sum: number) => sum / coordinates.length);

              const html = `
                <div style="font-family: 'Overpass', system-ui; padding:6px 4px; color:#fff;">
                  <div><b>Polygon Selection</b></div>
                  <div style="color:#B8C0DD; font-size:12px">${
                    filteredData.features.length
                  } data points within polygon</div>
                  <div style="color:#9AA3C0; font-size:11px">Center: (${center[1].toFixed(
                    5
                  )}, ${center[0].toFixed(5)})</div>
                </div>
              `;
              new maplibregl.Popup({ closeButton: true, maxWidth: "260px" })
                .setLngLat(center)
                .addTo(map);
            }
          }
        });

        map.on("draw.delete", () => {
          if (selectionMode === "polygon") {
            // Clear heatmap when polygon is deleted
            const heatmapSource = map.getSource(
              HEATMAP_SOURCE
            ) as maplibregl.GeoJSONSource;
            if (heatmapSource) {
              heatmapSource.setData({
                type: "FeatureCollection",
                features: [],
              });
            }
            setCurrentSelection(null);
          }
        });
      }

      function ensureHeatmapLayer() {
        if (!map.getSource(HEATMAP_SOURCE)) {
          map.addSource(HEATMAP_SOURCE, {
            type: "geojson",
            data: { type: "FeatureCollection", features: [] },
          });

          map.addLayer({
            id: HEATMAP_LAYER,
            type: "heatmap",
            source: HEATMAP_SOURCE,
            maxzoom: 15,
            paint: {
              "heatmap-weight": [
                "interpolate",
                ["linear"],
                ["get", "value"],
                0,
                0,
                50,
                0.5,
                100,
                1,
              ],
              "heatmap-intensity": [
                "interpolate",
                ["linear"],
                ["zoom"],
                0,
                1,
                15,
                3,
              ],
              "heatmap-color": [
                "interpolate",
                ["linear"],
                ["heatmap-density"],
                0,
                "rgba(33,102,172,0)",
                0.2,
                "rgb(103,169,207)",
                0.4,
                "rgb(209,229,240)",
                0.6,
                "rgb(253,219,199)",
                0.8,
                "rgb(239,138,98)",
                1,
                "rgb(178,24,43)",
              ],
              "heatmap-radius": [
                "interpolate",
                ["linear"],
                ["zoom"],
                0,
                2,
                15,
                20,
              ],
              "heatmap-opacity": 0.7,
            },
          });
        }
      }

      const debounced = debounce(loadForCurrentView, 400);
      const boot = () => {
        ensureSelectionLayer();
        ensureHeatmapLayer();
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
      } catch {}
      mapRef.current?.remove();
      mapRef.current = null;
      if (divRef.current) delete (divRef.current as any).__maplibre_initialized;
    };
  }, [
    pollutant,
    fetcher,
    center,
    zoom,
    selectionMode,
    onClearSelection,
    onResetView,
  ]);

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

  // Handle selection mode changes
  useLayoutEffect(() => {
    const map = mapRef.current;
    const draw = drawRef.current;
    if (!map || !draw) return;

    if (selectionMode === "polygon") {
      draw.changeMode("draw_polygon");
      map.getCanvas().style.cursor = "crosshair";
    } else {
      draw.changeMode("simple_select");
      map.getCanvas().style.cursor = "crosshair";
    }
  }, [selectionMode]);

  // Handle clear selection
  useLayoutEffect(() => {
    if (onClearSelection) {
      const map = mapRef.current;
      const draw = drawRef.current;
      if (!map || !draw) return;

      const clearSelection = () => {
        // Clear selection marker
        const selSource = map.getSource(SEL_SOURCE) as maplibregl.GeoJSONSource;
        if (selSource) {
          selSource.setData({ type: "FeatureCollection", features: [] });
        }

        // Clear heatmap
        const heatmapSource = map.getSource(
          HEATMAP_SOURCE
        ) as maplibregl.GeoJSONSource;
        if (heatmapSource) {
          heatmapSource.setData({ type: "FeatureCollection", features: [] });
        }

        // Clear drawn features
        draw.deleteAll();

        setCurrentSelection(null);
      };

      // Store the function for external access
      (map as any)._clearSelection = clearSelection;
    }
  }, [onClearSelection]);

  // Handle reset view
  useLayoutEffect(() => {
    if (onResetView) {
      const map = mapRef.current;
      if (!map) return;

      const resetView = () => {
        map.flyTo({
          center,
          zoom,
          essential: true,
        });
      };

      // Store the function for external access
      (map as any)._resetView = resetView;
    }
  }, [onResetView, center, zoom]);

  return (
    <div
      ref={divRef}
      className="relative w-full h-[calc(100vh-64px)] z-0 bg-spaceapps-gradient"
      aria-label="Vista de mapa con mediciones de calidad del aire"
      role="region"
    />
  );
});

MapView.displayName = "MapView";

export default MapView;
