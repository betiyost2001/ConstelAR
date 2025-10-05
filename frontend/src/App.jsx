import { useState } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Footer from "./components/Footer";
import Header from "./components/Header";
import MapView from "./components/MapView";
import Legend from "./components/Legend";
import PollutantsPage from "./components/PollutantsPage";
import ProjectPage from "./components/ProjetPaje";
import { DEFAULT_POLLUTANT } from "./constants/pollutants";
import "./index.css";

function MapShell() {
  const [pollutant, setPollutant] = useState("");
  return (
    <div className="flex-1 flex flex-col overflow-hidden relative">
      <MapView pollutant={pollutant || DEFAULT_POLLUTANT} />
      <Legend pollutant={pollutant} onChange={setPollutant} />
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="app h-screen flex flex-col">
        <Header />
        <Routes>
          <Route path="/" element={<MapShell />} />
          <Route path="/contaminantes" element={<PollutantsPage />} />
          <Route path="/proyecto" element={<ProjectPage />} />
          {/* compat con tu ruta vieja */}
          <Route path="/nosotros" element={<ProjectPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        <Footer />
      </div>
    </BrowserRouter>
  );
}
