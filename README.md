## 🌌 ContelAR — NASA Space Apps Challenge 2025  

**ContelAR** es una aplicación web que integra datos satelitales de la misión **TEMPO (Tropospheric Emissions: Monitoring Pollution)** junto con mediciones terrestres y variables meteorológicas, para mostrar en tiempo casi real la **calidad del aire en Norteamérica**.  

El proyecto busca ofrecer **pronósticos accesibles** y **alertas tempranas** de contaminación, contribuyendo a la **prevención en salud pública** y a la **concientización ciudadana**.  

---

## 📍 About the project (English version)  

**ContelAR** is a web application that integrates satellite data from the **TEMPO mission (Tropospheric Emissions: Monitoring Pollution)** together with ground-based measurements and meteorological variables, to display near real-time **air quality information across North America**.  

The project aims to deliver **accessible forecasts** and **early alerts** about air pollution, supporting **public health prevention** and **citizen awareness**.  

## Run the project (produdction or development)
- Run the terminal
- Do `Docker compose up -d --build`
- Go to localhost:8080 for the frontend
- Go to localhost:8000 for the backend

---

## 📅 Avances entregados – Etapa 1 / Delivered progress – Stage 1  

- **Infraestructura / Infrastructure**  
  - Docker Compose (dev & prod).  
  - Backend CORS configuration.  
  - `.env` variables for Vite.  

- **Backend (FastAPI)**  
  - Endpoints `/openaq/normalized` and `/openaq/latest`.  
  - Swagger enabled at `http://localhost:8000/docs`.  
  - Adapter for OpenAQ / Open-Meteo data.  

- **Frontend (React + Vite)**  
  - Initial setup with Chakra UI + MUI.  
  - `<MapView>` component with MapLibre and point layers.  
  - Basic popup with pollutant and value.  
  - `<Legend>` component with color ranges.  
  - Pollutant selector in `<Header>`.  

- **Funcionalidad clave / Key features**  
  - Dynamic visualization of air quality by pollutant.  
  - Cached results to reduce latency.  

- **Documentación / Documentation**  
  - Initial README with execution steps.  
  - Notes on CORS and `.env` setup.  

---

## 📅 Avances entregados – Etapa 2 / Delivered progress – Stage 2  

- **Interacción en el mapa / Map interaction**  
  - New selection mode: click anywhere on the map to query pollution at that point.  
  - Dynamic circle replaces static marker.  

- **Mejoras en datos / Data improvements**  
  - Correct pollutant filtering (e.g., O₃ shown as ozone).  
  - Colors adapted to ranges in `constants/aqi.js`.  
  - Cached point queries (`fetchAtPoint`) for faster responses.  

- **UI/UX**  
  - Popup enriched with value, unit, date, and coordinates.  
  - Removed “stiff” marker that duplicated on viewport move.  

- **Refactor técnico / Technical refactor**  
  - Better listener handling to avoid duplicates in HMR.  
  - Adjustments in `MapView.jsx` and `api.js`.  
  - Safe style loading (`map.once("idle", ...)`).  

- **Documentación / Documentation**  
  - README updated with Stage 2 progress.  

---

## 📅 Próximos pasos / Next steps  

- Dashboard with historical pollutant charts.  
- Basic unit tests in backend and frontend.  
- Deployment to a cloud service (Render, Railway, or AWS).  
- Refine UI: responsive design and user experience improvements.  

---

## 👩‍🚀 Equipo / Team  

We are **ContelAR**, a diverse team of students and professionals passionate about science and technology:  

- **Betina Yost** – Ingeniería en Sistemas (Córdoba) | Frontend, coordination, documentation.  
- **Agustina Fiorella Silva** – Ingeniería en Sistemas (Córdoba) | Backend, APIs.  
- **Kevin Agustín Ruiz** – Ingeniería en Sistemas (Buenos Aires) | Frontend & Backend.  
- **Ludmila Gandur** – Physics student | Research and documentation.  
- **Trinidad Bernardez** – Secondary school student (future astrophysicist) | Research and communication.  
- **Eduardo Alejandro Ponce Cobos** – Systems Engineer, Backend developer (10+ years experience).  

This combination of **academic diversity**, **professional expertise**, and **motivation to learn** allows us to approach the challenge from multiple perspectives, balancing technical rigor with creativity and innovation.  

---

## 🛠️ Tecnologías y herramientas / Tech & Tools  

**Frontend**: React + Vite, Chakra UI/MUI, MapLibre GL, PWA  
**Backend**: FastAPI, xarray/dask, SQLite, Tippecanoe  
**Data**: NASA TEMPO (EarthData, Harmony, CMR), AirNow, OpenAQ, HRRR/GFS  
**Infraestructura / Infra**: Docker, Google Cloud Run / AWS ECS, GitHub Actions  
**Colaboración / Collaboration**: GitHub, Trello, Google Drive, Figma  

---

## 📄 Licencia / License  

This project is developed as part of the **NASA Space Apps Challenge 2025**.  
Educational and non-commercial use only.  

