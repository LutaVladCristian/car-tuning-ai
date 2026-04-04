from fastapi import FastAPI

from app.routers import auth, photos, segmentation

app = FastAPI(
    title="Car Tuning AI — Backend MS",
    version="1.0.0",
    description="Authenticated gateway for car-segmentation-ms with photo history.",
)

app.include_router(auth.router)
app.include_router(segmentation.router)
app.include_router(photos.router)


@app.get("/health", tags=["meta"])
async def health() -> dict:
    return {"status": "ok"}
