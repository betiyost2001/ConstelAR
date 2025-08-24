from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import openaq

app = FastAPI(title="ArgentinaSpace API")
# CORS y routers:
# app.include_router(openaq_router, prefix="/openaq")

from fastapi.middleware.cors import CORSMiddleware

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
    "http://localhost:5175",
    "http://127.0.0.1:5175",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(openaq.router, prefix="/openaq")
@app.get("/")
def health():
    return {"status": "ok"}

