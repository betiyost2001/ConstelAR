## 🐳 Ejecutar con Docker
Dev (hot-reload) – Frontend + Backend
# desde la raíz del repo
docker compose -f docker-compose.dev.yml up --build


Frontend (Vite): http://localhost:5173

Backend (Swagger): http://localhost:8000/docs

Parar: Ctrl + C

Limpiar: docker compose -f docker-compose.dev.yml down

Notas dev

El frontend usa VITE_API_URL=http://api:8000 (nombre del servicio en la red Docker).

CORS en backend debe permitir http://localhost:5173.

Prod (build + Nginx para el front)
# desde la raíz del repo
docker compose up --build -d


Web (frontend build): http://localhost:8080

API: http://localhost:8000/docs

Logs: docker compose logs -f

Apagar: docker compose down

Notas prod

El build del front se hace con VITE_API_URL=http://api:8000 (definido en docker-compose.yml).

Si el puerto 8080 está ocupado, cambiá a 8081:80.

## 🧪 Ejecutar sin Docker (opcional)
Backend (FastAPI)
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
# Swagger → http://localhost:8000/docs

Frontend (Vite)
cd frontend
npm install
# opcional: crear .env con:
# VITE_API_URL=http://localhost:8000
npm run dev -- --host
# http://localhost:5173

## ⚙️ Variables y archivos útiles

frontend/.env (local opcional)

VITE_API_URL=http://localhost:8000


backend CORS (main.py)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173","http://localhost:8080"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

## 🧰 Problemas comunes

“docker: command not found” → instalar/abrir Docker Desktop y WSL2.

Puerto en uso → cambia puertos en docker-compose*.yml (ej. 8001:8000, 8081:80).

El front pega a la API equivocada → revisá VITE_API_URL (dev: http://api:8000; local fuera de Docker: http://localhost:8000).

Swagger muestra valores viejos → refresco duro del navegador (Ctrl+F5) y reiniciar backend.