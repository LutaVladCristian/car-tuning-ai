from fastapi import APIRouter, Depends, HTTPException
from firebase_admin.exceptions import FirebaseError
from sqlalchemy.orm import Session

from app.core.security import verify_firebase_token
from app.db.models.user import User
from app.schemas.auth import FirebaseAuthRequest, UserResponse
from dependencies import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/firebase", response_model=UserResponse)
async def firebase_auth(
    payload: FirebaseAuthRequest, db: Session = Depends(get_db)
) -> UserResponse:
    """Exchange a Firebase ID token for a synced backend user record."""
    try:
        claims = verify_firebase_token(payload.id_token)
    except FirebaseError as exc:
        raise HTTPException(status_code=401, detail=f"Invalid Firebase token: {exc}")

    uid: str = claims["uid"]
    email: str = claims.get("email", "")
    display_name: str | None = claims.get("name")

    user = db.query(User).filter(User.firebase_uid == uid).first()
    if user is None:
        user = User(firebase_uid=uid, email=email, display_name=display_name)
        db.add(user)
    else:
        # Keep email and display name in sync with Firebase.
        user.email = email
        user.display_name = display_name

    db.commit()
    db.refresh(user)
    return user
