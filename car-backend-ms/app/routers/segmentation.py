import struct
import time
from dataclasses import dataclass
from io import BytesIO

import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.models.photo import OperationType, Photo, PhotoStatus
from app.db.models.user import User
from app.services import proxy_service, storage_service
from config import get_settings
from dependencies import get_current_user, get_db

router = APIRouter(tags=["segmentation"])

_PASSTHROUGH_SEGMENTATION_ERRORS = {
    "No car is detected by the YOLO model.",
    "OpenAI rejected the prepared image or mask. Please try another image.",
}
_MAX_FILE_BYTES = 10 * 1024 * 1024
_MAX_IMAGE_DIMENSION = 4096
_MAX_IMAGE_PIXELS = _MAX_IMAGE_DIMENSION * _MAX_IMAGE_DIMENSION
_MAX_PROMPT_LEN = 1000
_ALLOWED_OUTPUT_SIZES = {"auto", "1024x1024", "1024x1536", "1536x1024"}
_RATE_LIMIT_WINDOW_SECONDS = 60 * 60
_edit_timestamps_by_uid: dict[str, list[float]] = {}


@dataclass(frozen=True)
class ValidatedUpload:
    content: bytes
    image_format: str
    mime_type: str
    width: int
    height: int


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
            return (
                int.from_bytes(content[offset + 5 : offset + 7], "big"),
                int.from_bytes(content[offset + 3 : offset + 5], "big"),
            )
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
    if chunk_type == b"VP8X":
        return int.from_bytes(content[24:27], "little") + 1, int.from_bytes(content[27:30], "little") + 1
    if chunk_type == b"VP8 ":
        return int.from_bytes(content[26:28], "little") & 0x3FFF, int.from_bytes(content[28:30], "little") & 0x3FFF
    if chunk_type == b"VP8L" and len(content) >= 25:
        bits = int.from_bytes(content[21:25], "little")
        return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
    return None


def _validate_upload_image(content: bytes) -> ValidatedUpload:
    if len(content) > _MAX_FILE_BYTES:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 10 MB.")
    png_dimensions = _png_dimensions(content)
    jpeg_dimensions = _jpeg_dimensions(content)
    webp_dimensions = _webp_dimensions(content)
    if png_dimensions is not None:
        image_format = "png"
        mime_type = "image/png"
        dimensions = png_dimensions
    elif jpeg_dimensions is not None:
        image_format = "jpeg"
        mime_type = "image/jpeg"
        dimensions = jpeg_dimensions
    elif webp_dimensions is not None:
        image_format = "webp"
        mime_type = "image/webp"
        dimensions = webp_dimensions
    else:
        raise HTTPException(status_code=415, detail="Unsupported or invalid image file. Upload a JPEG, PNG, or WEBP file.")
    width, height = dimensions
    if width < 1 or height < 1 or width > _MAX_IMAGE_DIMENSION or height > _MAX_IMAGE_DIMENSION or width * height > _MAX_IMAGE_PIXELS:
        raise HTTPException(status_code=413, detail=f"Image dimensions are too large. Maximum is {_MAX_IMAGE_DIMENSION}px per side and {_MAX_IMAGE_PIXELS} pixels total.")
    return ValidatedUpload(
        content=content,
        image_format=image_format,
        mime_type=mime_type,
        width=width,
        height=height,
    )


def _validate_edit_params(prompt: str, size: str) -> tuple[str, str]:
    prompt = prompt.strip()
    if not prompt:
        raise HTTPException(status_code=422, detail="Prompt must not be empty.")
    if len(prompt) > _MAX_PROMPT_LEN:
        raise HTTPException(status_code=422, detail=f"Prompt must be {_MAX_PROMPT_LEN} characters or fewer.")
    normalized_size = size.strip().lower()
    if normalized_size not in _ALLOWED_OUTPUT_SIZES:
        raise HTTPException(status_code=422, detail=f"Unsupported size. Allowed values: {', '.join(sorted(_ALLOWED_OUTPUT_SIZES))}.")
    return prompt, normalized_size


def _check_edit_rate_limit(firebase_uid: str) -> None:
    limit = get_settings().EDIT_PHOTO_RATE_LIMIT_PER_HOUR
    if limit < 1:
        return
    now = time.monotonic()
    timestamps = [ts for ts in _edit_timestamps_by_uid.get(firebase_uid, []) if ts >= now - _RATE_LIMIT_WINDOW_SECONDS]
    if len(timestamps) >= limit:
        _edit_timestamps_by_uid[firebase_uid] = timestamps
        raise HTTPException(status_code=429, detail="Edit rate limit exceeded. Try again later.")
    _edit_timestamps_by_uid[firebase_uid] = [*timestamps, now]


def _proxy_error(exc: Exception) -> HTTPException:
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        try:
            service_detail = exc.response.json().get("detail")
        except ValueError:
            service_detail = None
        if service_detail in _PASSTHROUGH_SEGMENTATION_ERRORS:
            return HTTPException(status_code=status, detail=service_detail)
        return HTTPException(status_code=status if 400 <= status < 500 else 502, detail=f"Segmentation service error: {status}")
    if isinstance(exc, httpx.RequestError):
        return HTTPException(status_code=502, detail="Segmentation service is unavailable.")
    return HTTPException(status_code=502, detail="Segmentation service returned an invalid response.")


def _owned_photo(photo_id: int, current_user: User, db: Session) -> Photo:
    photo = db.query(Photo).filter(Photo.id == photo_id, Photo.user_id == current_user.id).first()
    if photo is None:
        raise HTTPException(status_code=404, detail="Photo not found")
    return photo


def _delete_preview(photo: Photo, db: Session) -> None:
    for path in (photo.original_image_path, photo.prepared_image_path, photo.raw_mask_image_path, photo.mask_image_path):
        storage_service.delete_photo(path)
    db.delete(photo)


@router.post("/edit-photo/preview")
async def preview_edit_photo(
    file: UploadFile = File(...),
    prompt: str = Form(...),
    edit_car: bool = Form(...),
    size: str = Form("auto"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, int]:
    upload = _validate_upload_image(await file.read())
    prompt, size = _validate_edit_params(prompt, size)
    _check_edit_rate_limit(current_user.firebase_uid)

    for draft in db.query(Photo).filter(Photo.user_id == current_user.id, Photo.status == PhotoStatus.preview).all():
        _delete_preview(draft, db)
    db.commit()

    try:
        prepared, raw_mask, mask = await proxy_service.forward_segment_photo(
            upload.content,
            file.filename or f"image.{upload.image_format}",
            upload.mime_type,
            edit_car,
            size,
        )
    except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as exc:
        raise _proxy_error(exc)

    uid = current_user.firebase_uid
    photo = Photo(
        user_id=current_user.id,
        original_filename=file.filename or "image.jpg",
        original_image_path=storage_service.upload_photo(uid, "original", upload.content),
        prepared_image_path=storage_service.upload_photo(uid, "prepared", prepared),
        raw_mask_image_path=storage_service.upload_photo(uid, "raw-mask", raw_mask),
        mask_image_path=storage_service.upload_photo(uid, "mask", mask),
        operation_type=OperationType.edit_photo,
        operation_params={"prompt": prompt, "edit_car": edit_car, "size": size},
        status=PhotoStatus.preview,
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)
    return {"photo_id": photo.id}


@router.post("/edit-photo/{photo_id}/generate")
async def generate_edit_photo(
    photo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    photo = _owned_photo(photo_id, current_user, db)
    if photo.status == PhotoStatus.completed and photo.result_image_path:
        return StreamingResponse(BytesIO(storage_service.download_photo(photo.result_image_path)), media_type="image/png")
    if photo.status != PhotoStatus.preview:
        raise HTTPException(status_code=409, detail="Photo preview is not ready for generation.")

    claimed = (
        db.query(Photo)
        .filter(Photo.id == photo.id, Photo.status == PhotoStatus.preview)
        .update({Photo.status: PhotoStatus.generating}, synchronize_session=False)
    )
    db.commit()
    if claimed != 1:
        raise HTTPException(status_code=409, detail="Photo preview is already being generated.")
    db.refresh(photo)
    params = photo.operation_params or {}
    prompt = params.get("prompt")
    size = params.get("size")
    if not isinstance(prompt, str) or not isinstance(size, str):
        photo.status = PhotoStatus.preview
        db.commit()
        raise HTTPException(status_code=409, detail="Photo preview is missing generation parameters.")
    try:
        result = await proxy_service.forward_generate_photo(
            storage_service.download_photo(photo.prepared_image_path),
            storage_service.download_photo(photo.mask_image_path),
            prompt,
            size,
        )
    except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as exc:
        photo.status = PhotoStatus.preview
        db.commit()
        raise _proxy_error(exc)

    photo.result_image_path = storage_service.upload_photo(current_user.firebase_uid, "result", result)
    photo.status = PhotoStatus.completed
    db.commit()
    return StreamingResponse(BytesIO(result), media_type="image/png")


@router.delete("/edit-photo/{photo_id}/preview", status_code=204)
async def delete_edit_preview(
    photo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    photo = _owned_photo(photo_id, current_user, db)
    if photo.status != PhotoStatus.preview:
        raise HTTPException(status_code=409, detail="Only unapproved previews can be deleted.")
    _delete_preview(photo, db)
    db.commit()
