// src/App.jsx
import { useState } from "react";
import Header from "./components/Header";
import MapView from "./components/MapView";
import Legend from "./components/Legend";
import "./App.css";

export default function App() {
  // estado global del contaminante activo
  const [pollutant, setPollutant] = useState("pm25"); // 'pm25' | 'pm10' | 'o3'

  return (
    <div className="app">
      <Header />

      {/* pequeño selector (podés moverlo al Header si querés) */}
      <div style={{ padding: 8 }}>
        <label style={{ marginRight: 8 }}>Contaminante:</label>
        <select
          value={pollutant}
          onChange={(e) => setPollutant(e.target.value)}
        >
          <option value="pm25">PM2.5</option>
          <option value="pm10">PM10</option>
          <option value="o3">O₃ (ozono)</option>
        </select>
      </div>

      {/* contenedor posicionado para superponer la leyenda sobre el mapa */}
      <div style={{ position: "relative" }}>
        <MapView pollutant={pollutant} />
        <Legend pollutant={pollutant} title={`${pollutant.toUpperCase()} (µg/m³)`} />
      </div>
    </div>
  );
}
