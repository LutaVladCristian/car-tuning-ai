import base64
import io
import os
import shutil
import tempfile

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from openai import OpenAI
from PIL import Image
from segmentation import segment_car, segment_car_part

# Initialize the FastAPI app
app = FastAPI()

# Retrieve OpenAI API Key securely
openai_key = os.getenv("OPENAI_API_KEY")
if openai_key is None:
    raise RuntimeError("Missing OpenAI API key")

# Initialize OpenAI client
client = OpenAI(api_key=openai_key)

# C2: Maximum prompt length accepted from clients.
_MAX_PROMPT_LEN = 1000

# M2: Valid range for car-part class IDs (YOLO COCO classes 0-79, with margin).
_MAX_CAR_PART_ID = 200


@app.post("/car-segmentation")
async def car_segmentation_sam(
    file: UploadFile = File(...),
    inverse: bool = Form(...),
):
    content = await file.read()

    # H1: segment_car raises ValueError when no car is detected.
    try:
        image_stream = segment_car(content, inverse)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    image = Image.fromarray(image_stream.astype("uint8"))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    return StreamingResponse(buffer, media_type="image/png")


@app.post("/car-part-segmentation")
async def segment_part(
    file: UploadFile = File(...),
    carPartId: int = Form(...),
    inverse: bool = Form(...),
):
    # M2: Validate car part ID range.
    if not (0 <= carPartId <= _MAX_CAR_PART_ID):
        raise HTTPException(
            status_code=422,
            detail=f"carPartId must be between 0 and {_MAX_CAR_PART_ID}.",
        )

    content = await file.read()

    try:
        image_stream = segment_car_part(content, carPartId, inverse)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    image = Image.fromarray(image_stream.astype("uint8"))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    return StreamingResponse(buffer, media_type="image/png")


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
    size: str = Form("1024x1536"),
):
    # C2: Sanitize the prompt.
    prompt = prompt.strip()

    content = await file.read()

    # C3 + H3: Use a per-request temp directory so concurrent requests cannot
    # overwrite each other's files, and clean it up unconditionally afterwards.
    tmp_dir = tempfile.mkdtemp()
    try:
        segment_car(content, edit_car, size, output_dir=tmp_dir)

        image_path = os.path.join(tmp_dir, "image.png")
        mask_path = os.path.join(tmp_dir, "mask.png")

        # C1: Use context managers so file descriptors are closed promptly.
        with open(image_path, "rb") as image_f, open(mask_path, "rb") as mask_f:
            result = client.images.edit(
                model="gpt-image-1",
                image=image_f,
                mask=mask_f,
                prompt=prompt,
                quality="high",
                size="1024x1536",
            )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    image_bytes = base64.b64decode(result.data[0].b64_json)

    return StreamingResponse(io.BytesIO(image_bytes), media_type="image/png")
