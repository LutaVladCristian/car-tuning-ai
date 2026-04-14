from io import BytesIO

import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.models.photo import OperationType, Photo
from app.db.models.user import User
from app.services import proxy_service
from dependencies import get_current_user, get_db

router = APIRouter(tags=["segmentation"])

# C5: Reject uploads larger than 10 MB before forwarding to the ML service.
_MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB


def _check_file(content: bytes) -> None:
    """C5 + H5: enforce size limit and validate image magic bytes."""
    if len(content) > _MAX_FILE_BYTES:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 10 MB.")

    # H5: Verify magic bytes so arbitrary files cannot be forwarded.
    is_jpeg = content[:3] == b"\xff\xd8\xff"
    is_png = content[:8] == b"\x89PNG\r\n\x1a\n"
    is_webp = content[:4] == b"RIFF" and content[8:12] == b"WEBP"
    if not (is_jpeg or is_png or is_webp):
        raise HTTPException(
            status_code=415,
            detail="Unsupported image format. Upload a JPEG, PNG, or WEBP file.",
        )


def _proxy_status(exc: httpx.HTTPStatusError) -> int:
    """M7: Pass 4xx errors through; convert 5xx to 502 Bad Gateway."""
    seg_status = exc.response.status_code
    return seg_status if 400 <= seg_status < 500 else 502


@router.post("/car-segmentation")
async def car_segmentation(
    file: UploadFile = File(...),
    inverse: bool = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    content = await file.read()
    _check_file(content)

    try:
        result_bytes = await proxy_service.forward_car_segmentation(
            content, file.filename or "image.jpg", inverse
        )
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=_proxy_status(exc),
            detail=f"Segmentation service error: {exc.response.status_code}",
        )

    photo = Photo(
        user_id=current_user.id,
        original_filename=file.filename or "image.jpg",
        original_image=content,
        result_image=result_bytes,
        operation_type=OperationType.car_segmentation,
        operation_params={"inverse": inverse},
    )
    db.add(photo)
    db.commit()

    return StreamingResponse(BytesIO(result_bytes), media_type="image/png")


@router.post("/car-part-segmentation")
async def car_part_segmentation(
    file: UploadFile = File(...),
    carPartId: int = Form(...),
    inverse: bool = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    content = await file.read()
    _check_file(content)

    try:
        result_bytes = await proxy_service.forward_car_part_segmentation(
            content, file.filename or "image.jpg", carPartId, inverse
        )
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=_proxy_status(exc),
            detail=f"Segmentation service error: {exc.response.status_code}",
        )

    photo = Photo(
        user_id=current_user.id,
        original_filename=file.filename or "image.jpg",
        original_image=content,
        result_image=result_bytes,
        operation_type=OperationType.car_part_segmentation,
        operation_params={"carPartId": carPartId, "inverse": inverse},
    )
    db.add(photo)
    db.commit()

    return StreamingResponse(BytesIO(result_bytes), media_type="image/png")


@router.post("/edit-photo")
async def edit_photo(
    file: UploadFile = File(...),
    prompt: str = Form(...),
    edit_car: bool = Form(...),
    size: str = Form("1024x1536"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    content = await file.read()
    _check_file(content)

    try:
        result_bytes = await proxy_service.forward_edit_photo(
            content, file.filename or "image.jpg", prompt, edit_car, size
        )
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=_proxy_status(exc),
            detail=f"Segmentation service error: {exc.response.status_code}",
        )

    photo = Photo(
        user_id=current_user.id,
        original_filename=file.filename or "image.jpg",
        original_image=content,
        result_image=result_bytes,
        operation_type=OperationType.edit_photo,
        operation_params={"prompt": prompt, "edit_car": edit_car, "size": size},
    )
    db.add(photo)
    db.commit()

    return StreamingResponse(BytesIO(result_bytes), media_type="image/png")
