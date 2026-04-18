"""firebase-auth-v2

Revision ID: c1d2e3f4a5b6
Revises: 45e90066957a
Create Date: 2026-04-18 00:00:00.000000

- Replaces username + hashed_password columns with firebase_uid + display_name.
- Narrows the operationtype enum to edit_photo only (PostgreSQL).
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'c1d2e3f4a5b6'
down_revision: str | None = '45e90066957a'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- users table ---
    op.add_column('users', sa.Column('firebase_uid', sa.String(length=128), nullable=True))
    op.add_column('users', sa.Column('display_name', sa.String(length=255), nullable=True))
    op.create_index(op.f('ix_users_firebase_uid'), 'users', ['firebase_uid'], unique=True)

    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_column('users', 'username')
    op.drop_column('users', 'hashed_password')

    # --- operationtype enum (PostgreSQL only) ---
    # Remove car_segmentation and car_part_segmentation; keep only edit_photo.
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute("ALTER TABLE photos ALTER COLUMN operation_type TYPE VARCHAR(50)")
        op.execute("DROP TYPE IF EXISTS operationtype")
        op.execute("CREATE TYPE operationtype AS ENUM ('edit_photo')")
        op.execute(
            "ALTER TABLE photos ALTER COLUMN operation_type "
            "TYPE operationtype USING operation_type::operationtype"
        )


def downgrade() -> None:
    # --- operationtype enum (PostgreSQL only) ---
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute("ALTER TABLE photos ALTER COLUMN operation_type TYPE VARCHAR(50)")
        op.execute("DROP TYPE IF EXISTS operationtype")
        op.execute(
            "CREATE TYPE operationtype AS ENUM "
            "('car_segmentation', 'car_part_segmentation', 'edit_photo')"
        )
        op.execute(
            "ALTER TABLE photos ALTER COLUMN operation_type "
            "TYPE operationtype USING operation_type::operationtype"
        )

    # --- users table ---
    op.drop_index(op.f('ix_users_firebase_uid'), table_name='users')
    op.drop_column('users', 'firebase_uid')
    op.drop_column('users', 'display_name')

    op.add_column('users', sa.Column('username', sa.String(length=50), nullable=False, server_default=''))
    op.add_column('users', sa.Column('hashed_password', sa.String(length=255), nullable=False, server_default=''))
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
