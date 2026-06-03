from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.domain import PhotoRecord, UserRecord
from app.schemas.photo import PhotoListResponse, PhotoResponse
from app.services import storage_service
from app.services.photo_store import AbstractPhotoStore
from dependencies import get_current_user, get_store

router = APIRouter(prefix="/photos", tags=["photos"])


def _get_owned_photo(photo_id: int, current_user: UserRecord, store: AbstractPhotoStore) -> PhotoRecord:
    photo = store.get_owned_photo(current_user.firebase_uid, photo_id)
    if photo is None:
        raise HTTPException(status_code=404, detail="Photo not found")
    return photo


@router.get("", response_model=PhotoListResponse)
async def list_photos(
    current_user: UserRecord = Depends(get_current_user),
    store: AbstractPhotoStore = Depends(get_store),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> PhotoListResponse:
    photos, total = store.list_completed_photos(current_user.firebase_uid, skip, limit)
    return PhotoListResponse(
        photos=[PhotoResponse.model_validate(p) for p in photos],
        total=total,
    )


@router.get("/{photo_id}/original")
async def download_original_photo(
    photo_id: int,
    current_user: UserRecord = Depends(get_current_user),
    store: AbstractPhotoStore = Depends(get_store),
) -> StreamingResponse:
    photo = _get_owned_photo(photo_id, current_user, store)
    data = storage_service.download_photo(photo.original_image_path)
    return StreamingResponse(BytesIO(data), media_type="image/png")


@router.get("/{photo_id}/mask/raw")
async def download_raw_mask(
    photo_id: int,
    current_user: UserRecord = Depends(get_current_user),
    store: AbstractPhotoStore = Depends(get_store),
) -> StreamingResponse:
    photo = _get_owned_photo(photo_id, current_user, store)
    if not photo.raw_mask_image_path:
        raise HTTPException(status_code=404, detail="Raw mask not found")
    return StreamingResponse(
        BytesIO(storage_service.download_photo(photo.raw_mask_image_path)),
        media_type="image/png",
    )


@router.get("/{photo_id}/mask/edit")
async def download_edit_mask(
    photo_id: int,
    current_user: UserRecord = Depends(get_current_user),
    store: AbstractPhotoStore = Depends(get_store),
) -> StreamingResponse:
    photo = _get_owned_photo(photo_id, current_user, store)
    if not photo.mask_image_path:
        raise HTTPException(status_code=404, detail="Edit mask not found")
    return StreamingResponse(
        BytesIO(storage_service.download_photo(photo.mask_image_path)),
        media_type="image/png",
    )


@router.get("/{photo_id}")
async def download_photo(
    photo_id: int,
    current_user: UserRecord = Depends(get_current_user),
    store: AbstractPhotoStore = Depends(get_store),
) -> StreamingResponse:
    photo = _get_owned_photo(photo_id, current_user, store)
    path = photo.result_image_path or photo.original_image_path
    data = storage_service.download_photo(path)
    return StreamingResponse(BytesIO(data), media_type="image/png")
