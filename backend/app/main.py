from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.openaq import router as openaq_router  # ← import relativo
from .api import openaq

app = FastAPI(title="ArgentinaSpace API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health():
    return {"status": "ok"}

app.include_router(openaq.router, prefix="/openaq")
