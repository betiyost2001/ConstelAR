import { useState } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Footer from "./components/Footer";
import Header from "./components/Header";
import MapView from "./components/MapView";
import Legend from "./components/Legend";
import PollutantsPage from "./components/PollutantsPage";
import ProjectPage from "./components/ProjetPaje";
import TempoPage from "./components/TempoPage"; 

import { DEFAULT_POLLUTANT } from "./constants/pollutants";
import "./index.css";

// Componente para el Layout del Mapa (NO DEBE TENER SCROLL EXTERNO)
function MapLayout() {
    const [pollutant, setPollutant] = useState("");
    return (
        // Ocupa todo el espacio restante (flex-1)
        <div className="flex-1 flex flex-col relative"> 
            
            {/* El div del mapa ocupa el espacio flexible restante */}
            <div className="flex-1" style={{ height: '100%' }}>
                <MapView pollutant={pollutant || DEFAULT_POLLUTANT} />
            </div>

            {/* La Leyenda tiene su altura natural */}
            <Legend pollutant={pollutant} onChange={setPollutant} />
        </div>
    );
}

// Componente Wrapper para páginas con contenido que SÍ necesita scroll
function ScrollablePageWrapper({ children }) {
    // Este div es el que tiene el scroll y el padding para las páginas de contenido
    return (
        <div className="flex-1 overflow-y-auto p-8"> 
            {children}
        </div>
    );
}

export default function App() {
  return (
    <BrowserRouter>
      {/* Contenedor principal: h-screen flex-col */}
      <div className="app h-screen flex flex-col"> 
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
            element={<ScrollablePageWrapper><PollutantsPage /></ScrollablePageWrapper>} 
          />
          <Route 
            path="/proyecto" 
            element={<ScrollablePageWrapper><ProjectPage /></ScrollablePageWrapper>} 
          />
          <Route 
            path="/tempo" 
            element={<ScrollablePageWrapper><TempoPage /></ScrollablePageWrapper>} 
          /> 
          
          {/* Rutas de compatibilidad */}
          <Route 
            path="/nosotros" 
            element={<ScrollablePageWrapper><ProjectPage /></ScrollablePageWrapper>} 
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        
        <Footer />
      </div>
    </BrowserRouter>
  );
}