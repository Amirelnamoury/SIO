"""photo profil artisan

Revision ID: a1b2c3d4e5f6
Revises: f6a7b8c9d0e1
Create Date: 2026-09-05
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "f6a7b8c9d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("artisans") as batch_op:
        batch_op.add_column(sa.Column("photo_profil_key", sa.String(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("artisans") as batch_op:
        batch_op.drop_column("photo_profil_key")
