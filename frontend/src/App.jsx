import { useState } from "react";
import Header from "./components/Header";
import MapView from "./components/MapView";
import Legend from "./components/Legend";
import "./App.css";

export default function App() {
  const [pollutant, setPollutant] = useState("pm25");

  return (
    <div className="app">
      <Header />
      {/* Contenedor posicionado: mapa + leyenda con selector integrado */}
      <div style={{ position: "relative" }}>
        <MapView pollutant={pollutant} />
        <Legend pollutant={pollutant} onPollutantChange={setPollutant} />
      </div>
    </div>
  );
}
