import { useState } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import Footer from "./components/Footer";
import Header from "./components/Header";
import MapView from "./components/MapView";
import Legend from "./components/Legend";
import PollutantsPage from "./components/PollutantsPage";
import ProjectPage from "./components/ProjetPaje";
import TempoPage from "./components/TempoPage";

import { DEFAULT_POLLUTANT } from "./constants/pollutants";
import { NORTH_AMERICA_BOUNDS } from "./lib/api";
import "./index.css";

// Componente para el Layout del Mapa (NO DEBE TENER SCROLL EXTERNO)
function MapLayout() {
  const [pollutant, setPollutant] = useState("");
  const [selectedBbox, setSelectedBbox] = useState([
    NORTH_AMERICA_BOUNDS.west,
    NORTH_AMERICA_BOUNDS.south,
    NORTH_AMERICA_BOUNDS.east,
    NORTH_AMERICA_BOUNDS.north,
  ]);

  const handleResetBbox = () => {
    setSelectedBbox([
      NORTH_AMERICA_BOUNDS.west,
      NORTH_AMERICA_BOUNDS.south,
      NORTH_AMERICA_BOUNDS.east,
      NORTH_AMERICA_BOUNDS.north,
    ]);
  };

  return (
    // Ocupa todo el espacio restante (flex-1)
    <div className="relative flex flex-col flex-1">
      {/* El div del mapa ocupa el espacio flexible restante */}
      <div className="flex-1" style={{ height: "100%" }}>
        <MapView
          pollutant={pollutant || DEFAULT_POLLUTANT}
          selectedBbox={selectedBbox}
          onBboxChange={setSelectedBbox}
        />
      </div>

      {/* La Leyenda tiene su altura natural */}
      <Legend
        pollutant={pollutant}
        onChange={setPollutant}
        onResetBbox={handleResetBbox}
      />
    </div>
  );
}

// Componente Wrapper para páginas con contenido que SÍ necesita scroll
function ScrollablePageWrapper({ children }) {
  // Este div es el que tiene el scroll y el padding para las páginas de contenido
  return <div className="flex-1 p-8 overflow-y-auto">{children}</div>;
}

export default function App() {
  return (
    <BrowserRouter>
      {/* Contenedor principal: h-screen flex-col */}
      <div className="flex flex-col h-screen app">
        <Header />

        {/*
          IMPORTANTE: Las rutas se renderizan directamente.
          Solo las páginas que necesiten scroll usan el ScrollablePageWrapper.
          Esto permite que MapLayout ocupe el espacio sin conflicto de overflow.
        */}
        <Routes>
          {/* RUTA PRINCIPAL (MAPA): NO USA WRAPPER DE SCROLL */}
          <Route path="/" element={<MapLayout />} />

          {/* RUTAS DE CONTENIDO: SÍ USAN WRAPPER DE SCROLL */}
          <Route
            path="/contaminantes"
            element={
              <ScrollablePageWrapper>
                <PollutantsPage />
              </ScrollablePageWrapper>
            }
          />
          <Route
            path="/proyecto"
            element={
              <ScrollablePageWrapper>
                <ProjectPage />
              </ScrollablePageWrapper>
            }
          />
          <Route
            path="/tempo"
            element={
              <ScrollablePageWrapper>
                <TempoPage />
              </ScrollablePageWrapper>
            }
          />

          {/* Rutas de compatibilidad */}
          <Route
            path="/nosotros"
            element={
              <ScrollablePageWrapper>
                <ProjectPage />
              </ScrollablePageWrapper>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>

        <Footer />
      </div>
      <ToastContainer />
    </BrowserRouter>
  );
}
