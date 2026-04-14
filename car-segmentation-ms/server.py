import base64
import io
import os

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import StreamingResponse
from openai import OpenAI
from PIL import Image
from segmentation import segment_car, segment_car_part, working_dir

# Initialize the FastAPI app
app = FastAPI()

# Retrieve OpenAI API Key securely
openai_key = os.getenv("OPENAI_API_KEY")
if openai_key is None:
    raise RuntimeError("Missing OpenAI API key")

# Initialize OpenAI client
client = OpenAI(api_key=openai_key)


@app.post("/car-segmentation")
async def car_segmentation_sam(
    file: UploadFile = File(...),
    inverse: bool = Form(...),
):

    content = await file.read()
    image_stream = segment_car(content, inverse)  # Perform car segmentation

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
    content = await file.read()
    image_stream = segment_car_part(content, carPartId, inverse)

    image = Image.fromarray(image_stream.astype("uint8"))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    return StreamingResponse(buffer, media_type="image/png")


@app.post("/edit-photo")
async def edit_photo(
        file: UploadFile = File(...),
        prompt: str = Form("Replace only the background of this image with a photorealistic, cinematic New York City street during winter. "
            "Keep the car exactly as it is using the provided mask. Do not alter the car, its wheels, or any part of its body. "
            "Make the color of the car as realistic as possible and black."
            "Ensure the background blends smoothly around the car, with natural lighting, ground texture, and shadows consistent with the scene. "
            "Avoid any visual gaps, black areas, or mismatched edges where the car meets the road. Maintain realism and correct camera perspective."
        ),
        edit_car: bool = Form(...),
        size: str = Form("1024x1536"),
):
    content = await file.read()
    segment_car(content, edit_car, size)

    image_path = os.path.join(working_dir, "image.png")
    mask_path = os.path.join(working_dir, "mask.png")

    print(image_path)
    print(mask_path)

    result = client.images.edit(
        model="gpt-image-1",
        image=open(image_path, "rb"),
        mask=open(mask_path, "rb"),
        prompt=prompt,
        quality="high",
        size="1024x1536"
    )

    image_bytes = base64.b64decode(result.data[0].b64_json)

    return StreamingResponse(io.BytesIO(image_bytes), media_type="image/png")
