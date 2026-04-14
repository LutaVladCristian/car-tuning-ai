from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, LargeBinary, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.user import User


class OperationType(StrEnum):
    car_segmentation = "car_segmentation"
    car_part_segmentation = "car_part_segmentation"
    edit_photo = "edit_photo"


class Photo(Base):
    __tablename__ = "photos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_image: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    result_image: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    operation_type: Mapped[OperationType] = mapped_column(
        Enum(OperationType), nullable=False
    )
    operation_params: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="photos")
