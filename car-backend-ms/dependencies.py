from functools import lru_cache

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin.exceptions import FirebaseError

from app.core.security import verify_firebase_token
from app.domain import UserRecord
from app.services.photo_store import AbstractPhotoStore, FirestorePhotoStore

# auto_error=False lets us return 401 (not 403) for missing Authorization headers.
bearer_scheme = HTTPBearer(auto_error=False)


@lru_cache
def get_store() -> AbstractPhotoStore:
    return FirestorePhotoStore()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    store: AbstractPhotoStore = Depends(get_store),
) -> UserRecord:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        claims = verify_firebase_token(credentials.credentials)
    except FirebaseError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    uid: str = claims["uid"]
    email = claims.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Firebase token is missing an email claim")
    return store.get_or_create_user(uid, email, claims.get("name"))
