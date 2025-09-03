# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging  # 👈 agregado

from .config import settings
from .db import engine, Base
from .routes import auth, notifications
from .middleware.rate_limit import limiter, rate_limit_handler

# Tu router existente
from app.api import openaq

# Crear tablas (solo útil en dev local con SQLite; en Docker usamos Alembic)
# Puedes comentar esto si querés depender 100% de Alembic:
# Base.metadata.create_all(bind=engine)

app = FastAPI(title="ArgentinaSpace API")

# CORS
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
]
# también agregamos lo que está en settings, por si tenés .env
for o in settings.ALLOWED_ORIGINS.split(","):
    if o and o not in origins:
        origins.append(o)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logger para startup
logger = logging.getLogger("uvicorn.error")  # 👈 agregado

# Rate limiting con Redis (tolerante a errores)
@app.on_event("startup")
async def _startup():
    try:
        await limiter.init(app)
    except Exception as e:
        logger.warning(f"Rate limiter deshabilitado: {e}")

app.state.limiter = limiter
app.add_exception_handler(429, rate_limit_handler)

# Routers existentes + nuevos
app.include_router(openaq.router, prefix="/openaq")
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(notifications.router, prefix="/notifications", tags=["notifications"])

@app.get("/")
def health():
    return {"status": "ok"}

@app.get("/healthz", include_in_schema=False)
def healthz():
    return {"ok": True}
