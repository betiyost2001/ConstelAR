## 🚀 Proyecto: ConstelAR — Air Quality (MVP)

Aplicación web que visualiza la **calidad del aire** en Córdoba (Argentina) usando
datos abiertos de OpenAQ / Open-Meteo y un backend propio en **FastAPI**.  (POR EL MOMENTO, hasta tener lo de TEMPO)
El frontend usa **React + Vite + MapLibre** para renderizar un mapa interactivo
con puntos de contaminación (PM₂․₅, O₃, NO₂, etc.) y leyendas dinámicas.

---

## 📅 Sprint 1 — Alcance entregado

- **Infraestructura**: Docker Compose (dev y prod), CORS configurado, `.env` para Vite.
- **Backend (FastAPI)**:
  - Endpoints `/openaq/normalized` y `/openaq/latest`.
  - Swagger habilitado en `http://localhost:8000/docs`.
  - Adaptador para datos de OpenAQ / Open-Meteo.
- **Frontend (React + Vite)**:
  - Configuración inicial con Chakra + MUI.
  - Componente `<MapView>` con MapLibre y capas de puntos.
  - Interacción básica: popup con contaminante y valor.
  - Componente `<Legend>` con rangos de colores.
  - Selector de contaminante en `<Header>`.
- **Funcionalidad clave**:
  - Visualización dinámica de calidad del aire por contaminante.
  - Cache de resultados para reducir latencia.
- **Documentación**:
  - README con pasos de ejecución en dev/prod/local.
  - Notas de configuración de CORS y `.env`.

---

## 📅 Sprint 2 — Alcance entregado

- **Interacción avanzada en mapa**:
  - Nuevo modo de selección: al hacer click en cualquier punto del mapa, se consulta
    la contaminación exacta en esas coordenadas.
  - Se reemplazó el marcador estático por un único círculo dinámico que se mueve con cada click.
- **Mejoras en los datos**:
  - Filtro correcto por contaminante (ej. O₃ ya devuelve ozono en vez de PM₂․₅).
  - Colores del punto clickeado adaptados al rango definido en `constants/aqi.js`.
  - Cache puntual (`fetchAtPoint`) para mejorar respuesta de consultas.
- **UI/UX**:
  - Popup enriquecido con valores, unidad, fecha y coordenadas.
  - Eliminado el punto “tieso” que se movía con el viewport (quedaba duplicado).
- **Refactor técnico**:
  - Manejo de listeners para evitar duplicados en HMR (desarrollo).
  - Ajustes en `MapView.jsx` y `api.js` para unificar la lógica de consultas.
  - Manejo seguro de carga de estilos (`map.once("idle", ...)`).
- **Documentación**:
  - Actualización del README con alcance del Sprint 2.

---

## 📅 Sprint 3 — Próximos pasos (plan)

- Dashboard con gráficas históricas por contaminante.
- Test unitarios básicos en backend y frontend.
- Deploy en servicio cloud (ej: Render, Railway o AWS).
- Refinar UI: diseño responsive y mejoras en la experiencia de usuario.
