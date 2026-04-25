import asyncio
import base64
import io
import os
import shutil
import threading
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from openai import OpenAI
from PIL import Image

openai_key = os.getenv("OPENAI_API_KEY")
if openai_key is None:
    raise RuntimeError("Missing OpenAI API key")

client = OpenAI(api_key=openai_key)
_MAX_PROMPT_LEN = 1000

_models_ready = threading.Event()
_segment_car = None
_working_dir = None


def _load_models() -> None:
    global _segment_car, _working_dir
    from download_models import download_models
    download_models()
    import segmentation as seg
    _segment_car = seg.segment_car
    _working_dir = seg.working_dir
    _models_ready.set()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load models in a background thread so the port opens immediately.
    # Cloud Run's TCP startup probe passes as soon as uvicorn binds the port.
    asyncio.create_task(asyncio.to_thread(_load_models))
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/health")
def health():
    if not _models_ready.is_set():
        raise HTTPException(status_code=503, detail="Models loading")
    return {"status": "ok"}


@app.post("/edit-photo")
async def edit_photo(
    file: UploadFile = File(...),
    prompt: str = Form(
        "Replace only the background of this image with a photorealistic, cinematic New York City street during winter. "
        "Keep the car exactly as it is using the provided mask. Do not alter the car, its wheels, or any part of its body. "
        "Make the color of the car as realistic as possible and black."
        "Ensure the background blends smoothly around the car, with natural lighting, ground texture, and shadows consistent with the scene. "
        "Avoid any visual gaps, black areas, or mismatched edges where the car meets the road. Maintain realism and correct camera perspective.",
        max_length=_MAX_PROMPT_LEN,
    ),
    edit_car: bool = Form(...),
    size: str = Form("auto"),
):
    if not _models_ready.is_set():
        raise HTTPException(status_code=503, detail="Models still loading, try again shortly")

    prompt = prompt.strip()
    size = size.strip().lower()

    content = await file.read()
    with Image.open(io.BytesIO(content)) as source_image:
        source_width, source_height = source_image.size
    preprocessing_size = None if size == "auto" else size

    os.makedirs(_working_dir, exist_ok=True)
    tmp_dir = os.path.join(_working_dir, f"request-{uuid.uuid4().hex}")
    os.makedirs(tmp_dir)
    try:
        try:
            _segment_car(content, edit_car, preprocessing_size, output_dir=tmp_dir)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

        image_path = os.path.join(tmp_dir, "image.png")
        mask_path = os.path.join(tmp_dir, "mask.png")

        with open(image_path, "rb") as image_f, open(mask_path, "rb") as mask_f:
            result = client.images.edit(
                model="gpt-image-1",
                image=image_f,
                mask=mask_f,
                prompt=prompt,
                quality="high",
                size=size,
            )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    image_bytes = base64.b64decode(result.data[0].b64_json)
    with Image.open(io.BytesIO(image_bytes)) as edited_image:
        if size == "auto" and edited_image.size != (source_width, source_height):
            resampling = Image.Resampling.LANCZOS
            edited_image = edited_image.resize((source_width, source_height), resampling)

        output = io.BytesIO()
        edited_image.save(output, format="PNG")
        output.seek(0)

    return StreamingResponse(output, media_type="image/png")
