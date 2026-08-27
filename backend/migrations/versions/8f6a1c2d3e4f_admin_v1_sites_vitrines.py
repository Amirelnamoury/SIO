"""admin v1 et sites vitrines

Revision ID: 8f6a1c2d3e4f
Revises: 42d3e0b23a14
Create Date: 2026-08-27
"""
from datetime import datetime, timezone
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8f6a1c2d3e4f"
down_revision: Union[str, None] = "42d3e0b23a14"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "admin_users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("nom", sa.String(), nullable=False),
        sa.Column("actif", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_admin_users_email"), "admin_users", ["email"], unique=True)
    op.create_index(op.f("ix_admin_users_id"), "admin_users", ["id"], unique=False)

    op.create_table(
        "sites_vitrines",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("artisan_id", sa.Integer(), nullable=False),
        sa.Column("statut", sa.String(), nullable=False),
        sa.Column("domaine", sa.String(), nullable=True),
        sa.Column("url_publique", sa.String(), nullable=True),
        sa.Column("storage_key", sa.String(), nullable=True),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("date_generation", sa.DateTime(timezone=True), nullable=True),
        sa.Column("date_publication", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["artisan_id"], ["artisans.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("artisan_id"),
    )
    op.create_index(op.f("ix_sites_vitrines_artisan_id"), "sites_vitrines", ["artisan_id"], unique=True)
    op.create_index(op.f("ix_sites_vitrines_id"), "sites_vitrines", ["id"], unique=False)

    connexion = op.get_bind()
    artisans = connexion.execute(sa.text(
        "SELECT id, site_statut, site_url, created_at FROM artisans "
        "WHERE site_url IS NOT NULL OR site_statut IN ('en_cours', 'livre')"
    )).fetchall()
    sites = sa.table(
        "sites_vitrines",
        sa.column("artisan_id", sa.Integer),
        sa.column("statut", sa.String),
        sa.column("url_publique", sa.String),
        sa.column("config", sa.JSON),
        sa.column("date_publication", sa.DateTime(timezone=True)),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    now = datetime.now(timezone.utc)
    for artisan_id, ancien_statut, site_url, artisan_created_at in artisans:
        statut = "publie" if ancien_statut == "livre" and site_url else "brouillon"
        connexion.execute(sites.insert().values(
            artisan_id=artisan_id,
            statut=statut,
            url_publique=site_url,
            config={},
            date_publication=None,
            created_at=artisan_created_at or now,
            updated_at=now,
        ))


def downgrade() -> None:
    op.drop_index(op.f("ix_sites_vitrines_id"), table_name="sites_vitrines")
    op.drop_index(op.f("ix_sites_vitrines_artisan_id"), table_name="sites_vitrines")
    op.drop_table("sites_vitrines")
    op.drop_index(op.f("ix_admin_users_id"), table_name="admin_users")
    op.drop_index(op.f("ix_admin_users_email"), table_name="admin_users")
    op.drop_table("admin_users")
