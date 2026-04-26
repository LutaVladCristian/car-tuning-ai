from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.models.photo import Photo
from app.db.models.user import User
from app.schemas.photo import PhotoListResponse, PhotoResponse
from app.services import storage_service
from dependencies import get_current_user, get_db

router = APIRouter(prefix="/photos", tags=["photos"])


def _get_owned_photo(photo_id: int, current_user: User, db: Session) -> Photo:
    photo = (
        db.query(Photo)
        .filter(Photo.id == photo_id, Photo.user_id == current_user.id)
        .first()
    )
    if photo is None:
        raise HTTPException(status_code=404, detail="Photo not found")
    return photo


@router.get("", response_model=PhotoListResponse)
async def list_photos(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> PhotoListResponse:
    query = db.query(Photo).filter(Photo.user_id == current_user.id)
    total = query.count()
    photos = query.order_by(Photo.created_at.desc()).offset(skip).limit(limit).all()
    return PhotoListResponse(
        photos=[PhotoResponse.model_validate(p) for p in photos],
        total=total,
    )


@router.get("/{photo_id}/original")
async def download_original_photo(
    photo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    photo = _get_owned_photo(photo_id, current_user, db)
    data = storage_service.download_photo(photo.original_image_path)
    return StreamingResponse(BytesIO(data), media_type="image/png")


@router.get("/{photo_id}")
async def download_photo(
    photo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    photo = _get_owned_photo(photo_id, current_user, db)
    path = photo.result_image_path or photo.original_image_path
    data = storage_service.download_photo(path)
    return StreamingResponse(BytesIO(data), media_type="image/png")
