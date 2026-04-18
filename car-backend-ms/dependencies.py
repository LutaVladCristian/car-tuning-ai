from collections.abc import Generator

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin.exceptions import FirebaseError
from sqlalchemy.orm import Session

from app.core.security import verify_firebase_token
from app.db.models.user import User
from app.db.session import SessionLocal

# auto_error=False lets us return 401 (not 403) for missing Authorization headers.
bearer_scheme = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        claims = verify_firebase_token(credentials.credentials)
    except FirebaseError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    uid: str = claims["uid"]
    user = db.query(User).filter(User.firebase_uid == uid).first()
    if user is None:
        # Auto-create on first authenticated request in case /auth/firebase was skipped.
        user = User(
            firebase_uid=uid,
            email=claims.get("email", ""),
            display_name=claims.get("name"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user
