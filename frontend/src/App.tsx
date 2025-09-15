import { useState, useCallback, useRef } from "react";
import Header from "./components/Header";
import MapView from "./components/MapView";
import Legend from "./components/Legend";

export type PollutantType = "pm25" | "pm10" | "o3" | "no2" | "so2" | "co";
export type SelectionMode = "point" | "polygon";

export interface MapViewRef {
  _clearSelection: () => void;
  _resetView: () => void;
}

export default function App(): React.ReactElement {
  const [pollutant, setPollutant] = useState<PollutantType>("pm25");
  const [selectionMode, setSelectionMode] = useState<SelectionMode>("point");
  const mapRef = useRef<MapViewRef>(null);

  const handleClearSelection = useCallback(() => {
    if (mapRef.current && mapRef.current._clearSelection) {
      mapRef.current._clearSelection();
    }
  }, []);

  const handleResetView = useCallback(() => {
    if (mapRef.current && mapRef.current._resetView) {
      mapRef.current._resetView();
    }
  }, []);

  return (
    <div className="min-h-screen bg-spaceapps-gradient">
      <Header />
      {/* Contenedor posicionado: mapa + leyenda con selector integrado */}
      <div className="relative">
        <MapView
          ref={mapRef}
          pollutant={pollutant}
          selectionMode={selectionMode}
          onClearSelection={handleClearSelection}
          onResetView={handleResetView}
        />
        <Legend
          pollutant={pollutant}
          onPollutantChange={setPollutant}
          selectionMode={selectionMode}
          onSelectionModeChange={setSelectionMode}
          onClearSelection={handleClearSelection}
          onResetView={handleResetView}
        />
      </div>
    </div>
  );
}
