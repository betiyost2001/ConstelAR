import { useState } from "react";
import Header from "./components/Header";
import FilterBar from "./components/FilterBar";
import MapView from "./components/MapView";
import Legend from "./components/Legend";
import "./App.css";
import { DEFAULT_POLLUTANT } from "./constants/pollutants";

export default function App() {
  const [pollutant, setPollutant] = useState(DEFAULT_POLLUTANT);

  return (
    <div className="app">
      <Header />
      {/* Contenedor posicionado: filtro + mapa + leyenda */}
      <div style={{ position: "relative" }}>
        <FilterBar pollutant={pollutant} onChange={setPollutant} />
        <MapView pollutant={pollutant} />
        <Legend pollutant={pollutant} />
      </div>
    </div>
  );
}
