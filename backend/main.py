import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import endpoints

app = FastAPI(
    title="Descale API",
    version="3.0.0",
    description="Image-scaling attacks for multi-modal prompt injection (research/education).",
)

# Local dev origins, plus any set via DESCALE_ALLOWED_ORIGINS (comma-separated)
# so the deployed API can accept the GitHub Pages frontend.
_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
]
_origins += [o.strip() for o in os.getenv("DESCALE_ALLOWED_ORIGINS", "").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(endpoints.router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "Descale backend is running", "docs": "/docs", "api": "/api/info"}
