import { useState } from "react";
import Header from "./components/Header";
import MapView from "./components/MapView";
import Legend from "./components/Legend";
import SubscriptionLegend from "./components/SubscriptionLegend";
import { DEFAULT_POLLUTANT } from "./constants/pollutants";
import "./index.css";

export default function App() {
  const [pollutant, setPollutant] = useState("");

  return (
    <div className="app h-screen flex flex-col">
      <Header />
      {/* Contenedor posicionado: filtro + mapa + leyenda */}
      <div className="flex-1 flex flex-col overflow-hidden relative">
        <MapView pollutant={pollutant || DEFAULT_POLLUTANT} />
        <Legend pollutant={pollutant} onChange={setPollutant} />
        <SubscriptionLegend position="bottom-left" />
      </div>
    </div>
  );
}
