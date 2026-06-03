from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class OperationType(StrEnum):
    edit_photo = "edit_photo"


class PhotoStatus(StrEnum):
    preview = "preview"
    generating = "generating"
    completed = "completed"


@dataclass(slots=True)
class UserRecord:
    id: int
    firebase_uid: str
    email: str
    display_name: str | None
    created_at: datetime


@dataclass(slots=True)
class PhotoRecord:
    id: int
    user_id: int
    original_filename: str
    original_image_path: str
    prepared_image_path: str | None
    result_image_path: str | None
    raw_mask_image_path: str | None
    mask_image_path: str | None
    status: PhotoStatus
    operation_type: OperationType
    operation_params: dict | None
    created_at: datetime
