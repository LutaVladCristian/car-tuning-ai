import uuid

from firebase_admin import storage

from app.core.security import _get_app


def upload_photo(firebase_uid: str, role: str, data: bytes) -> str:
    """Upload image bytes to Firebase Storage, return the blob path."""
    _get_app()
    path = f"users/{firebase_uid}/photos/{uuid.uuid4().hex}/{role}.png"
    blob = storage.bucket().blob(path)
    blob.upload_from_string(data, content_type="image/png")
    return path


def download_photo(path: str) -> bytes:
    """Download and return raw bytes for a stored photo blob path."""
    _get_app()
    return storage.bucket().blob(path).download_as_bytes()
