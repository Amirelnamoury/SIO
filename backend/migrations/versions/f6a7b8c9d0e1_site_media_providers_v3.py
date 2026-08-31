"""site media provider metadata and result cache

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    columns = (
        sa.Column("provider", sa.String(), nullable=True),
        sa.Column("provider_asset_id", sa.String(), nullable=True),
        sa.Column("photographer", sa.String(), nullable=True),
        sa.Column("source_url", sa.String(), nullable=True),
        sa.Column("provider_url", sa.String(), nullable=True),
        sa.Column("query", sa.String(), nullable=True),
        sa.Column("licence_metadata", sa.JSON(), nullable=True),
        sa.Column("times_used", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
    )
    for column in columns:
        op.add_column("site_media_library", column)
    for column in ("provider", "provider_asset_id", "last_used_at"):
        op.create_index(op.f(f"ix_site_media_library_{column}"), "site_media_library", [column], unique=False)
    op.create_table(
        "site_media_provider_cache",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("query_key", sa.String(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "query_key", name="uq_site_media_provider_cache_query"),
    )
    for column in ("id", "provider", "query_key", "expires_at"):
        op.create_index(op.f(f"ix_site_media_provider_cache_{column}"), "site_media_provider_cache", [column], unique=column == "id")


def downgrade() -> None:
    for column in ("expires_at", "query_key", "provider", "id"):
        op.drop_index(op.f(f"ix_site_media_provider_cache_{column}"), table_name="site_media_provider_cache")
    op.drop_table("site_media_provider_cache")
    for column in ("last_used_at", "provider_asset_id", "provider"):
        op.drop_index(op.f(f"ix_site_media_library_{column}"), table_name="site_media_library")
    for column in ("last_used_at", "times_used", "licence_metadata", "query", "provider_url", "source_url", "photographer", "provider_asset_id", "provider"):
        op.drop_column("site_media_library", column)
