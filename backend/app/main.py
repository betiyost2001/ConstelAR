from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import openaq   # asumimos que acá está tu router

app = FastAPI(title="ArgentinaSpace API")

# Routers
app.include_router(openaq.router, prefix="/openaq")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health():
    return {"status": "ok"}
