import secrets
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext

from config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

JWT_SECRET_KEY=secrets.token_hex(32)

def create_access_token(subject: str) -> str:
    settings = get_settings()
    expire = datetime.now(UTC) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")


def decode_access_token(token: str) -> str:
    payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
    sub: str = payload.get("sub")
    if sub is None:
        raise JWTError("Missing subject in token")
    return sub
