from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, photos, segmentation
from config import get_settings

app = FastAPI(
    title="Car Tuning AI — Backend MS",
    version="1.0.0",
    description="Authenticated gateway for car-segmentation-ms with photo history.",
)

settings = get_settings()

# C7: Origins read from env so production URLs need no code change.
# L1: Restrict to the methods and headers the frontend actually uses.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth.router)
app.include_router(segmentation.router)
app.include_router(photos.router)


@app.get("/health", tags=["meta"])
async def health() -> dict:
    return {"status": "ok"}
