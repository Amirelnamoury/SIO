"""notifications des demandes issues des sites vitrines

Revision ID: b5d7e9f1a3c2
Revises: 8f6a1c2d3e4f
Create Date: 2026-08-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b5d7e9f1a3c2"
down_revision: Union[str, None] = "8f6a1c2d3e4f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("artisan_id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=True),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("titre", sa.String(), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("view", sa.String(), nullable=False),
        sa.Column("lu", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["artisan_id"], ["artisans.id"]),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_notifications_artisan_id"), "notifications", ["artisan_id"], unique=False)
    op.create_index(op.f("ix_notifications_client_id"), "notifications", ["client_id"], unique=False)
    op.create_index(op.f("ix_notifications_created_at"), "notifications", ["created_at"], unique=False)
    op.create_index(op.f("ix_notifications_id"), "notifications", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_notifications_id"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_created_at"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_client_id"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_artisan_id"), table_name="notifications")
    op.drop_table("notifications")
