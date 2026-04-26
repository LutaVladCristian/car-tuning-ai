import struct
import time
from io import BytesIO

import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.models.photo import OperationType, Photo
from app.db.models.user import User
from app.services import proxy_service, storage_service
from config import get_settings
from dependencies import get_current_user, get_db

router = APIRouter(tags=["segmentation"])

# C5: Reject uploads larger than 10 MB before forwarding to the ML service.
_MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB
_MAX_IMAGE_DIMENSION = 4096
_MAX_IMAGE_PIXELS = _MAX_IMAGE_DIMENSION * _MAX_IMAGE_DIMENSION
_MAX_PROMPT_LEN = 1000
_ALLOWED_OUTPUT_SIZES = {"auto", "1024x1024", "1024x1536", "1536x1024"}
_RATE_LIMIT_WINDOW_SECONDS = 60 * 60
_edit_timestamps_by_uid: dict[str, list[float]] = {}


def _jpeg_dimensions(content: bytes) -> tuple[int, int] | None:
    if len(content) < 4 or content[:2] != b"\xff\xd8":
        return None

    offset = 2
    while offset + 9 < len(content):
        if content[offset] != 0xFF:
            offset += 1
            continue
        while offset < len(content) and content[offset] == 0xFF:
            offset += 1
        if offset >= len(content):
            return None

        marker = content[offset]
        offset += 1
        if marker in {0xD8, 0xD9} or 0xD0 <= marker <= 0xD7:
            continue
        if offset + 2 > len(content):
            return None

        segment_length = int.from_bytes(content[offset : offset + 2], "big")
        if segment_length < 2 or offset + segment_length > len(content):
            return None
        if marker in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}:
            if segment_length < 7:
                return None
            height = int.from_bytes(content[offset + 3 : offset + 5], "big")
            width = int.from_bytes(content[offset + 5 : offset + 7], "big")
            return width, height
        offset += segment_length

    return None


def _png_dimensions(content: bytes) -> tuple[int, int] | None:
    if len(content) < 24 or content[:8] != b"\x89PNG\r\n\x1a\n" or content[12:16] != b"IHDR":
        return None
    return struct.unpack(">II", content[16:24])


def _webp_dimensions(content: bytes) -> tuple[int, int] | None:
    if len(content) < 30 or content[:4] != b"RIFF" or content[8:12] != b"WEBP":
        return None

    chunk_type = content[12:16]
    if chunk_type == b"VP8X" and len(content) >= 30:
        width = int.from_bytes(content[24:27], "little") + 1
        height = int.from_bytes(content[27:30], "little") + 1
        return width, height
    if chunk_type == b"VP8 " and len(content) >= 30:
        width = int.from_bytes(content[26:28], "little") & 0x3FFF
        height = int.from_bytes(content[28:30], "little") & 0x3FFF
        return width, height
    if chunk_type == b"VP8L" and len(content) >= 25:
        bits = int.from_bytes(content[21:25], "little")
        width = (bits & 0x3FFF) + 1
        height = ((bits >> 14) & 0x3FFF) + 1
        return width, height

    return None


def _image_dimensions(content: bytes) -> tuple[int, int] | None:
    return _png_dimensions(content) or _jpeg_dimensions(content) or _webp_dimensions(content)


def _check_file(content: bytes) -> None:
    """Enforce size, type, and dimensions before forwarding to the ML service."""
    if len(content) > _MAX_FILE_BYTES:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 10 MB.")

    dimensions = _image_dimensions(content)
    if dimensions is None:
        raise HTTPException(
            status_code=415,
            detail="Unsupported or invalid image file. Upload a JPEG, PNG, or WEBP file.",
        )

    width, height = dimensions
    if (
        width < 1
        or height < 1
        or width > _MAX_IMAGE_DIMENSION
        or height > _MAX_IMAGE_DIMENSION
        or width * height > _MAX_IMAGE_PIXELS
    ):
        raise HTTPException(
            status_code=413,
            detail=(
                "Image dimensions are too large. "
                f"Maximum is {_MAX_IMAGE_DIMENSION}px per side and {_MAX_IMAGE_PIXELS} pixels total."
            ),
        )


def _validate_edit_params(prompt: str, size: str) -> tuple[str, str]:
    prompt = prompt.strip()
    if not prompt:
        raise HTTPException(status_code=422, detail="Prompt must not be empty.")
    if len(prompt) > _MAX_PROMPT_LEN:
        raise HTTPException(
            status_code=422,
            detail=f"Prompt must be {_MAX_PROMPT_LEN} characters or fewer.",
        )

    normalized_size = size.strip().lower()
    if normalized_size not in _ALLOWED_OUTPUT_SIZES:
        allowed = ", ".join(sorted(_ALLOWED_OUTPUT_SIZES))
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported size. Allowed values: {allowed}.",
        )
    return prompt, normalized_size


def _check_edit_rate_limit(firebase_uid: str) -> None:
    limit = get_settings().EDIT_PHOTO_RATE_LIMIT_PER_HOUR
    if limit < 1:
        return

    now = time.monotonic()
    cutoff = now - _RATE_LIMIT_WINDOW_SECONDS
    timestamps = [ts for ts in _edit_timestamps_by_uid.get(firebase_uid, []) if ts >= cutoff]
    if len(timestamps) >= limit:
        _edit_timestamps_by_uid[firebase_uid] = timestamps
        raise HTTPException(status_code=429, detail="Edit rate limit exceeded. Try again later.")

    timestamps.append(now)
    _edit_timestamps_by_uid[firebase_uid] = timestamps


def _proxy_status(exc: httpx.HTTPStatusError) -> int:
    """M7: Pass 4xx errors through; convert 5xx to 502 Bad Gateway."""
    seg_status = exc.response.status_code
    return seg_status if 400 <= seg_status < 500 else 502


@router.post("/edit-photo")
async def edit_photo(
    file: UploadFile = File(...),
    prompt: str = Form(...),
    edit_car: bool = Form(...),
    size: str = Form("auto"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    content = await file.read()
    _check_file(content)
    prompt, size = _validate_edit_params(prompt, size)
    _check_edit_rate_limit(current_user.firebase_uid)

    try:
        result_bytes, mask_bytes = await proxy_service.forward_edit_photo(
            content, file.filename or "image.jpg", prompt, edit_car, size
        )
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=_proxy_status(exc),
            detail=f"Segmentation service error: {exc.response.status_code}",
        )
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Segmentation service is unavailable.")
    except ValueError:
        raise HTTPException(status_code=502, detail="Segmentation service returned an invalid response.")

    uid = current_user.firebase_uid
    original_path = storage_service.upload_photo(uid, "original", content)
    result_path = storage_service.upload_photo(uid, "result", result_bytes)
    mask_path = storage_service.upload_photo(uid, "mask", mask_bytes)

    photo = Photo(
        user_id=current_user.id,
        original_filename=file.filename or "image.jpg",
        original_image_path=original_path,
        result_image_path=result_path,
        mask_image_path=mask_path,
        operation_type=OperationType.edit_photo,
        operation_params={"prompt": prompt, "edit_car": edit_car, "size": size},
    )
    db.add(photo)
    db.commit()

    return StreamingResponse(BytesIO(result_bytes), media_type="image/png")
