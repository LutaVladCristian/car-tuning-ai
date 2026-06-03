import logging

from fastapi import APIRouter, Depends, HTTPException
from firebase_admin.exceptions import FirebaseError
from google.api_core.exceptions import GoogleAPICallError

from app.core.security import verify_firebase_token
from app.schemas.auth import FirebaseAuthRequest, UserResponse
from app.services.photo_store import AbstractPhotoStore
from dependencies import get_store

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


@router.post("/firebase", response_model=UserResponse)
async def firebase_auth(
    payload: FirebaseAuthRequest, store: AbstractPhotoStore = Depends(get_store)
) -> UserResponse:
    """Exchange a Firebase ID token for a synced backend user record."""
    try:
        claims = verify_firebase_token(payload.id_token)
    except FirebaseError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    uid: str = claims["uid"]
    email: str | None = claims.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Firebase token is missing an email claim")
    display_name: str | None = claims.get("name")
    try:
        return store.sync_user(uid, email, display_name)
    except GoogleAPICallError:
        logger.exception("Failed to sync Firebase user with Firestore.")
        raise HTTPException(status_code=503, detail="Authentication store is unavailable.")
