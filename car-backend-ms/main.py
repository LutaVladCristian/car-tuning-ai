from pathlib import Path

from fastapi import FastAPI

from app.routers import auth, photos, segmentation
from config import get_settings

settings = get_settings()

app = FastAPI(
    title="Car Tuning AI — Backend MS",
    version="1.0.0",
    description="Authenticated gateway for car-segmentation-ms with photo history.",
)

app.include_router(auth.router)
app.include_router(segmentation.router)
app.include_router(photos.router)


@app.on_event("startup")
async def startup() -> None:
    Path(settings.STORAGE_BASE_PATH).mkdir(parents=True, exist_ok=True)


@app.get("/health", tags=["meta"])
async def health() -> dict:
    return {"status": "ok"}
