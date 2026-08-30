"""medias des sites vitrines

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-08-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "site_media_library",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("media_id", sa.String(), nullable=False),
        sa.Column("metier", sa.String(), nullable=False),
        sa.Column("sous_categorie", sa.String(), nullable=False),
        sa.Column("storage_key", sa.String(), nullable=False),
        sa.Column("thumbnail_key", sa.String(), nullable=True),
        sa.Column("mime_type", sa.String(), nullable=False),
        sa.Column("largeur", sa.Integer(), nullable=True),
        sa.Column("hauteur", sa.Integer(), nullable=True),
        sa.Column("orientation", sa.String(), nullable=False),
        sa.Column("usage_recommande", sa.JSON(), nullable=False),
        sa.Column("licence", sa.String(), nullable=False),
        sa.Column("source_nom", sa.String(), nullable=False),
        sa.Column("credit", sa.String(), nullable=True),
        sa.Column("actif", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("media_id"),
        sa.UniqueConstraint("storage_key"),
        sa.UniqueConstraint("thumbnail_key"),
    )
    for column in ("id", "media_id", "metier", "sous_categorie"):
        op.create_index(op.f(f"ix_site_media_library_{column}"), "site_media_library", [column], unique=column == "media_id")

    op.create_table(
        "site_medias",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("artisan_id", sa.Integer(), nullable=False),
        sa.Column("site_vitrine_id", sa.Integer(), nullable=True),
        sa.Column("type_media", sa.String(), nullable=False),
        sa.Column("categorie", sa.String(), nullable=True),
        sa.Column("storage_key", sa.String(), nullable=False),
        sa.Column("thumbnail_key", sa.String(), nullable=False),
        sa.Column("nom_original", sa.String(), nullable=False),
        sa.Column("mime_type", sa.String(), nullable=False),
        sa.Column("taille_octets", sa.Integer(), nullable=False),
        sa.Column("largeur", sa.Integer(), nullable=True),
        sa.Column("hauteur", sa.Integer(), nullable=True),
        sa.Column("ordre", sa.Integer(), nullable=False),
        sa.Column("actif", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("alt_text", sa.String(), nullable=True),
        sa.Column("checksum", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["artisan_id"], ["artisans.id"]),
        sa.ForeignKeyConstraint(["site_vitrine_id"], ["sites_vitrines.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("storage_key"),
        sa.UniqueConstraint("thumbnail_key"),
    )
    for column in ("id", "artisan_id", "site_vitrine_id", "type_media", "categorie", "checksum", "created_at"):
        op.create_index(op.f(f"ix_site_medias_{column}"), "site_medias", [column], unique=False)

    op.create_table(
        "site_media_selections",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("site_vitrine_id", sa.Integer(), nullable=False),
        sa.Column("usage", sa.String(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("site_media_id", sa.Integer(), nullable=True),
        sa.Column("library_media_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "(source = 'artisan' AND site_media_id IS NOT NULL AND library_media_id IS NULL) OR "
            "(source = 'bibliotheque' AND library_media_id IS NOT NULL AND site_media_id IS NULL) OR "
            "(source = 'fallback' AND site_media_id IS NULL AND library_media_id IS NULL)",
            name="ck_site_media_selection_source",
        ),
        sa.ForeignKeyConstraint(["library_media_id"], ["site_media_library.id"]),
        sa.ForeignKeyConstraint(["site_media_id"], ["site_medias.id"]),
        sa.ForeignKeyConstraint(["site_vitrine_id"], ["sites_vitrines.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("site_vitrine_id", "usage", "position", name="uq_site_media_selection_usage_position"),
    )
    for column in ("id", "site_vitrine_id", "usage", "site_media_id", "library_media_id"):
        op.create_index(op.f(f"ix_site_media_selections_{column}"), "site_media_selections", [column], unique=False)

    op.create_table(
        "site_media_usages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("artisan_id", sa.Integer(), nullable=False),
        sa.Column("site_vitrine_id", sa.Integer(), nullable=False),
        sa.Column("library_media_id", sa.Integer(), nullable=False),
        sa.Column("usage", sa.String(), nullable=False),
        sa.Column("selected_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["artisan_id"], ["artisans.id"]),
        sa.ForeignKeyConstraint(["library_media_id"], ["site_media_library.id"]),
        sa.ForeignKeyConstraint(["site_vitrine_id"], ["sites_vitrines.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("id", "artisan_id", "site_vitrine_id", "library_media_id", "usage", "selected_at"):
        op.create_index(op.f(f"ix_site_media_usages_{column}"), "site_media_usages", [column], unique=False)


def downgrade() -> None:
    for column in ("selected_at", "usage", "library_media_id", "site_vitrine_id", "artisan_id", "id"):
        op.drop_index(op.f(f"ix_site_media_usages_{column}"), table_name="site_media_usages")
    op.drop_table("site_media_usages")
    for column in ("library_media_id", "site_media_id", "usage", "site_vitrine_id", "id"):
        op.drop_index(op.f(f"ix_site_media_selections_{column}"), table_name="site_media_selections")
    op.drop_table("site_media_selections")
    for column in ("created_at", "checksum", "categorie", "type_media", "site_vitrine_id", "artisan_id", "id"):
        op.drop_index(op.f(f"ix_site_medias_{column}"), table_name="site_medias")
    op.drop_table("site_medias")
    for column in ("sous_categorie", "metier", "media_id", "id"):
        op.drop_index(op.f(f"ix_site_media_library_{column}"), table_name="site_media_library")
    op.drop_table("site_media_library")
