"""blob-to-storage-path

Revision ID: a1b2c3d4e5f6
Revises: f3a1b2c4d5e6
Create Date: 2026-04-25 00:00:00.000000

- Replaces original_image / result_image LargeBinary columns with
  original_image_path / result_image_path VARCHAR columns.
  Images are now stored in Firebase Storage; the DB keeps only the GCS path.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'a1b2c3d4e5f6'
down_revision: str | None = 'f3a1b2c4d5e6'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add path columns. server_default='' lets the ALTER succeed on rows that
    # existed before this migration; the default is removed immediately after.
    op.add_column('photos', sa.Column(
        'original_image_path', sa.String(), server_default='', nullable=False
    ))
    op.alter_column('photos', 'original_image_path', server_default=None)
    op.add_column('photos', sa.Column('result_image_path', sa.String(), nullable=True))

    op.drop_column('photos', 'original_image')
    op.drop_column('photos', 'result_image')


def downgrade() -> None:
    op.add_column('photos', sa.Column('original_image', sa.LargeBinary(), nullable=True))
    op.add_column('photos', sa.Column('result_image', sa.LargeBinary(), nullable=True))

    op.drop_column('photos', 'result_image_path')
    op.drop_column('photos', 'original_image_path')
