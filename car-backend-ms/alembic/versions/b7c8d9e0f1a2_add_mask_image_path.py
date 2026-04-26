"""add-mask-image-path

Revision ID: b7c8d9e0f1a2
Revises: a1b2c3d4e5f6
Create Date: 2026-04-26 14:50:00.000000

Adds the optional Firebase Storage path for the segmentation mask saved with
each edit result.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b7c8d9e0f1a2"
down_revision: str | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("photos", sa.Column("mask_image_path", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("photos", "mask_image_path")
