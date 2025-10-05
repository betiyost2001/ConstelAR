## 🚀 ConstelAR – Resumen del Proyecto
** ConstelAR ** es una aplicación web creada para el NASA Space Apps Challenge 2025 que visualiza la calidad del aire en tiempo casi real utilizando datos satelitales de la misión NASA TEMPO (Tropospheric Emissions: Monitoring Pollution).

Su objetivo es ofrecer una herramienta accesible para explorar mediciones de contaminantes clave (NO2, SO2, O3, HCHO) sobre Norteamérica, buscando generar alertas tempranas y conciencia pública.

# 🌐 Funcionalidades Clave
Visualización en Mapa: Muestra la calidad del aire por área o por punto geográfico.
Contaminantes: NO2, SO2, O3 y Formaldehído (HCHO).

Backend API (FastAPI): Gestiona la autenticación, descarga de granules TEMPO (vía earthaccess) y normalización de datos.
Frontend (React/Vite/MapLibre): Interfaz simple para la exploración y visualización coloreada de las mediciones.

# 🛠️ Quick Start (Local Development)
La opción recomendada es usando Docker Compose.

Copia variables de entorno:

cp backend/.env.example backend/.env
# (Opcional) Completa EARTHDATA_TOKEN en backend/.env
Levanta los servicios:


docker compose -f docker-compose.dev.yml up -d --build
Frontend: http://localhost:5173

Backend Docs: http://localhost:8000/docs

💻 Arquitectura y Datos
Backend: FastAPI + earthaccess (para NASA Earthdata), procesando y sirviendo datos vía el endpoint principal: GET /api/v1/tempo/normalized.

Frontend: React + Vite + MapLibre, que convierte los datos planos del backend a GeoJSON para colorear el mapa según umbrales de AQI (Air Quality Index).

Rendimiento: El backend implementa cache de granules (TEMPO_CACHE_DIR) y se recomienda restringir las consultas a áreas pequeñas (radius≤30 km) y periodos recientes (∼24−48 h).

🗺️ Roadmap Futuro
Implementación de Notificaciones por niveles altos de contaminantes.

Integración de Pronósticos y modelos de dispersión.

Persistencia de datos históricos en una DB.

Mejoras de UX y Accesibilidad.

## 🇬🇧 ConstelAR – Project Summary (English)
** ConstelAR ** is a web application developed for the NASA Space Apps Challenge 2025 that visualizes near real-time air quality using NASA TEMPO mission satellite data (Tropospheric Emissions: Monitoring Pollution).

The goal is to provide an accessible tool to explore measurements of key pollutants (NO2, SO2, O3, HCHO) over North America, aiming to generate early alerts and raise public awareness.

# 🌐 Key Features
Map Visualization: Displays air quality by area or specific geographical point.

Pollutants: (NO2, SO2, O3, and Formaldehyde (HCHO).

Backend API (FastAPI): Manages authentication, TEMPO granule downloads (via earthaccess), and data normalization.

Frontend (React/Vite/MapLibre): Simple interface for exploration and colored visualization of the measurements.

# 🛠️ Quick Start (Local Development)
The recommended option is using Docker Compose.

Copy environment variables:

cp backend/.env.example backend/.env
# (Optional) Fill in EARTHDATA_TOKEN in backend/.env
Bring up services:

docker compose -f docker-compose.dev.yml up -d --build
Frontend: http://localhost:5173

Backend Docs: http://localhost:8000/docs

💻 Architecture and Data
Backend: FastAPI + earthaccess (for NASA Earthdata), processing and serving data via the main endpoint: GET /api/v1/tempo/normalized.

Frontend: React + Vite + MapLibre, converting flat backend data to GeoJSON for coloring the map based on AQI (Air Quality Index) thresholds.

Performance: The backend implements granule caching (TEMPO_CACHE_DIR), and it's recommended to restrict queries to small areas (radius≤30 km) and recent periods (∼24−48 h).

# 🗺️ Future Roadmap
Implementation of Notifications for high pollutant levels.

Integration of Forecasts and dispersion models.
Persistence of historical data in a DB.
UX and Accessibility improvements.
**Infraestructura / Infra**: Docker, Google Cloud Run / AWS ECS, GitHub Actions  
**Colaboración / Collaboration**: GitHub, Trello, Google Drive, Figma  

---

## 📄 Licencia / License  

This project is developed as part of the **NASA Space Apps Challenge 2025**.  
Educational and non-commercial use only.  

