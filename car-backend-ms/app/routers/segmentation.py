from io import BytesIO

import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.db.models.photo import OperationType, Photo
from app.db.models.user import User
from app.services import proxy_service
from dependencies import get_current_user, get_db

router = APIRouter(tags=["segmentation"])


@router.post("/car-segmentation")
async def car_segmentation(
    file: UploadFile = File(...),
    inverse: bool = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    content = await file.read()

    try:
        result_bytes = await proxy_service.forward_car_segmentation(
            content, file.filename or "image.jpg", inverse
        )
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"Segmentation service error: {exc.response.status_code}")

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

    try:
        result_bytes = await proxy_service.forward_car_part_segmentation(
            content, file.filename or "image.jpg", carPartId, inverse
        )
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"Segmentation service error: {exc.response.status_code}")

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
) -> JSONResponse:
    content = await file.read()

    try:
        result = await proxy_service.forward_edit_photo(
            content, file.filename or "image.jpg", prompt, edit_car, size
        )
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"Segmentation service error: {exc.response.status_code}")

    photo = Photo(
        user_id=current_user.id,
        original_filename=file.filename or "image.jpg",
        original_image=content,
        result_image=None,
        operation_type=OperationType.edit_photo,
        operation_params={"prompt": prompt, "edit_car": edit_car, "size": size},
    )
    db.add(photo)
    db.commit()

    return JSONResponse(result)
