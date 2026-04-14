from datetime import datetime

from pydantic import BaseModel

from app.db.models.photo import OperationType


class PhotoResponse(BaseModel):
    id: int
    user_id: int
    original_filename: str
    operation_type: OperationType
    operation_params: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PhotoListResponse(BaseModel):
    photos: list[PhotoResponse]
    total: int
