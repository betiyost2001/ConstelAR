from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import openaq

app = FastAPI(title="ArgentinaSpace API")

# CORS para el front en dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health():
    return {"ok": True}

app.include_router(openaq.router, prefix="/openaq")
