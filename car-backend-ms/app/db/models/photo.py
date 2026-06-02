from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.user import User


class OperationType(StrEnum):
    edit_photo = "edit_photo"


class PhotoStatus(StrEnum):
    preview = "preview"
    generating = "generating"
    completed = "completed"


class Photo(Base):
    __tablename__ = "photos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_image_path: Mapped[str] = mapped_column(String, nullable=False)
    prepared_image_path: Mapped[str | None] = mapped_column(String, nullable=True)
    result_image_path: Mapped[str | None] = mapped_column(String, nullable=True)
    raw_mask_image_path: Mapped[str | None] = mapped_column(String, nullable=True)
    mask_image_path: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[PhotoStatus] = mapped_column(
        Enum(PhotoStatus), nullable=False, default=PhotoStatus.completed
    )
    operation_type: Mapped[OperationType] = mapped_column(
        Enum(OperationType), nullable=False
    )
    operation_params: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="photos")
