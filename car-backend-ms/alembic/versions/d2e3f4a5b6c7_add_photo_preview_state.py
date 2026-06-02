"""add-photo-preview-state

Revision ID: d2e3f4a5b6c7
Revises: b7c8d9e0f1a2
Create Date: 2026-06-02 00:00:00.000000
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d2e3f4a5b6c7"
down_revision: str | None = "b7c8d9e0f1a2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    photo_status = sa.Enum("preview", "generating", "completed", name="photostatus")
    photo_status.create(op.get_bind(), checkfirst=True)
    op.add_column("photos", sa.Column("prepared_image_path", sa.String(), nullable=True))
    op.add_column("photos", sa.Column("raw_mask_image_path", sa.String(), nullable=True))
    op.add_column(
        "photos",
        sa.Column("status", photo_status, server_default="completed", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("photos", "status")
    op.drop_column("photos", "raw_mask_image_path")
    op.drop_column("photos", "prepared_image_path")
    sa.Enum("preview", "generating", "completed", name="photostatus").drop(
        op.get_bind(), checkfirst=True
    )
