import asyncio
import base64
import io
import logging
import os
import shutil
import threading
import uuid
import warnings
from contextlib import asynccontextmanager
from dataclasses import dataclass

from dotenv import find_dotenv, load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from openai import APIError, BadRequestError, OpenAI
from PIL import Image, UnidentifiedImageError

load_dotenv(find_dotenv())

openai_key = os.getenv("OPENAI_API_KEY")
if openai_key is None:
    raise RuntimeError("Missing OpenAI API key")

client = OpenAI(api_key=openai_key)
logger = logging.getLogger(__name__)
_MAX_PROMPT_LEN = 1000
_MAX_IMAGE_DIMENSION = 4096
_MAX_IMAGE_PIXELS = _MAX_IMAGE_DIMENSION * _MAX_IMAGE_DIMENSION
_MAX_SEGMENT_UPLOAD_BYTES = 10 * 1024 * 1024
_MAX_OPENAI_IMAGE_BYTES = 50 * 1024 * 1024
_MAX_OPENAI_MASK_BYTES = 4 * 1024 * 1024
_ALLOWED_OUTPUT_SIZES = {"auto", "1024x1024", "1024x1536", "1536x1024"}
_ALLOWED_SOURCE_FORMATS = {
    "JPEG": "image/jpeg",
    "PNG": "image/png",
    "WEBP": "image/webp",
}
Image.MAX_IMAGE_PIXELS = _MAX_IMAGE_PIXELS
warnings.simplefilter("error", Image.DecompressionBombWarning)

_models_ready = threading.Event()
_segment_car = None
_working_dir = None


@dataclass(frozen=True)
class ValidatedImage:
    image_format: str
    mime_type: str
    width: int
    height: int
    has_alpha: bool


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


def _validate_size(size: str) -> str:
    normalized_size = size.strip().lower()
    if normalized_size not in _ALLOWED_OUTPUT_SIZES:
        allowed = ", ".join(sorted(_ALLOWED_OUTPUT_SIZES))
        raise HTTPException(status_code=422, detail=f"Unsupported size. Allowed values: {allowed}.")
    return normalized_size


def _image_size_error() -> HTTPException:
    return HTTPException(
        status_code=413,
        detail=(
            "Image dimensions are too large. "
            f"Maximum is {_MAX_IMAGE_DIMENSION}px per side and {_MAX_IMAGE_PIXELS} pixels total."
        ),
    )


def _has_alpha_channel(image: Image.Image) -> bool:
    if "A" in image.getbands():
        return True
    transparency = image.info.get("transparency")
    return transparency is not None


def _inspect_image(content: bytes, *, allowed_formats: dict[str, str], invalid_detail: str) -> ValidatedImage:
    try:
        with Image.open(io.BytesIO(content)) as source_image:
            image_format = source_image.format
            if image_format not in allowed_formats:
                raise HTTPException(status_code=415, detail=invalid_detail)
            source_width, source_height = source_image.size
            if (
                source_width < 1
                or source_height < 1
                or source_width > _MAX_IMAGE_DIMENSION
                or source_height > _MAX_IMAGE_DIMENSION
                or source_width * source_height > _MAX_IMAGE_PIXELS
            ):
                raise _image_size_error()
            has_alpha = _has_alpha_channel(source_image)
            source_image.verify()
            return ValidatedImage(
                image_format=image_format,
                mime_type=allowed_formats[image_format],
                width=source_width,
                height=source_height,
                has_alpha=has_alpha,
            )
    except HTTPException:
        raise
    except (Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise _image_size_error()
    except (UnidentifiedImageError, OSError):
        raise HTTPException(status_code=415, detail=invalid_detail)


@app.get("/health")
def health():
    if not _models_ready.is_set():
        raise HTTPException(status_code=503, detail="Models loading")
    return {"status": "ok"}


def _validate_payload_size(content: bytes, max_bytes: int, detail: str) -> None:
    if len(content) > max_bytes:
        raise HTTPException(status_code=413, detail=detail)


def _validate_source_upload(content: bytes) -> ValidatedImage:
    _validate_payload_size(content, _MAX_SEGMENT_UPLOAD_BYTES, "File too large. Maximum size is 10 MB.")
    return _inspect_image(
        content,
        allowed_formats=_ALLOWED_SOURCE_FORMATS,
        invalid_detail="Unsupported or invalid image file. Upload a JPEG, PNG, or WEBP file.",
    )


def _validate_generation_source(content: bytes) -> ValidatedImage:
    _validate_payload_size(content, _MAX_OPENAI_IMAGE_BYTES, "Prepared image is too large for image generation.")
    return _inspect_image(
        content,
        allowed_formats=_ALLOWED_SOURCE_FORMATS,
        invalid_detail="Unsupported or invalid prepared image file. Upload a JPEG, PNG, or WEBP file.",
    )


def _validate_generation_mask(content: bytes) -> ValidatedImage:
    _validate_payload_size(content, _MAX_OPENAI_MASK_BYTES, "Mask image is too large. Maximum size is 4 MB.")
    mask = _inspect_image(
        content,
        allowed_formats={"PNG": "image/png"},
        invalid_detail="Invalid mask image. Upload a PNG file with an alpha channel.",
    )
    if not mask.has_alpha:
        raise HTTPException(status_code=422, detail="Invalid mask image. Upload a PNG file with an alpha channel.")
    return mask


@app.post("/segment-photo")
async def segment_photo(
    file: UploadFile = File(...),
    edit_car: bool = Form(...),
    size: str = Form("auto"),
):
    if not _models_ready.is_set():
        raise HTTPException(status_code=503, detail="Models still loading, try again shortly")

    size = _validate_size(size)

    content = await file.read()
    _validate_source_upload(content)
    preprocessing_size = None if size == "auto" else size

    os.makedirs(_working_dir, exist_ok=True)
    tmp_dir = os.path.join(_working_dir, f"request-{uuid.uuid4().hex}")
    os.makedirs(tmp_dir)
    try:
        try:
            _segment_car(content, edit_car, preprocessing_size, output_dir=tmp_dir)
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc))

        image_path = os.path.join(tmp_dir, "image.png")
        mask_path = os.path.join(tmp_dir, "mask.png")
        raw_mask_path = os.path.join(tmp_dir, "raw-mask.png")
        with (
            open(image_path, "rb") as image_f,
            open(mask_path, "rb") as mask_f,
            open(raw_mask_path, "rb") as raw_mask_f,
        ):
            image_bytes = image_f.read()
            mask_bytes = mask_f.read()
            raw_mask_bytes = raw_mask_f.read()
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return JSONResponse({
        "image_b64": base64.b64encode(image_bytes).decode(),
        "raw_mask_b64": base64.b64encode(raw_mask_bytes).decode(),
        "mask_b64": base64.b64encode(mask_bytes).decode(),
    })


@app.post("/generate-photo")
async def generate_photo(
    file: UploadFile = File(...),
    mask: UploadFile = File(...),
    prompt: str = Form(..., max_length=_MAX_PROMPT_LEN),
    size: str = Form("auto"),
):
    if not _models_ready.is_set():
        raise HTTPException(status_code=503, detail="Models still loading, try again shortly")

    prompt = prompt.strip()
    if not prompt:
        raise HTTPException(status_code=422, detail="Prompt must not be empty.")
    size = _validate_size(size)

    image_content = await file.read()
    mask_content = await mask.read()
    source = _validate_generation_source(image_content)
    mask_image = _validate_generation_mask(mask_content)
    if (source.width, source.height) != (mask_image.width, mask_image.height):
        raise HTTPException(status_code=422, detail="Prepared image and mask must have exactly the same dimensions.")

    try:
        result = client.images.edit(
            model="gpt-image-1",
            image=("image.png", image_content, "image/png"),
            mask=("mask.png", mask_content, "image/png"),
            prompt=prompt,
            quality="high",
            input_fidelity="high",
            size=size,
        )
    except BadRequestError as exc:
        logger.warning("OpenAI rejected prepared image edit request: %s", exc)
        raise HTTPException(
            status_code=502,
            detail="OpenAI rejected the prepared image or mask. Please try another image.",
        ) from exc
    except APIError as exc:
        logger.exception("OpenAI image generation request failed")
        raise HTTPException(
            status_code=502,
            detail="Image generation provider is unavailable right now. Please try again.",
        ) from exc

    image_bytes = base64.b64decode(result.data[0].b64_json)
    try:
        edited_image_ctx = Image.open(io.BytesIO(image_bytes))
    except (UnidentifiedImageError, OSError):
        raise HTTPException(status_code=502, detail="Image provider returned invalid image data.")

    with edited_image_ctx as edited_image:
        if size == "auto" and edited_image.size != (source.width, source.height):
            resampling = Image.Resampling.LANCZOS
            edited_image = edited_image.resize((source.width, source.height), resampling)

        output = io.BytesIO()
        edited_image.save(output, format="PNG")
        result_png_bytes = output.getvalue()

    return JSONResponse({
        "result_b64": base64.b64encode(result_png_bytes).decode(),
    })
