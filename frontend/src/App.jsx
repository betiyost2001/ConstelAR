import { useState } from "react";
import Header from "./components/Header";
import FilterBar from "./components/FilterBar";
import MapView from "./components/MapView";
import Legend from "./components/Legend";
import { DEFAULT_POLLUTANT } from "./constants/pollutants";

export default function App() {
  const [pollutant, setPollutant] = useState(DEFAULT_POLLUTANT);

  return (
    <div className="app h-screen flex flex-col">
      <Header />
      {/* Contenedor posicionado: filtro + mapa + leyenda */}
      <div className="flex-1 flex flex-col overflow-hidden relative">
        <FilterBar pollutant={pollutant} onChange={setPollutant} />
        <MapView pollutant={pollutant} />
        <Legend pollutant={pollutant} />
      </div>
    </div>
  );
}
