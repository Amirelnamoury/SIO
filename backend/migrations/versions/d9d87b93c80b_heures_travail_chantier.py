"""heures_travail chantier

Revision ID: d9d87b93c80b
Revises: 7e066477f1a8
Create Date: 2026-08-26 00:28:00.313486

Note : genere vide par --autogenerate car la base de dev locale avait deja
la table (creee par le filet de securite create_all() au demarrage - voir
app/main.py). Corps ecrit a la main pour rester correct sur une base qui n'a
jamais tourne create_all() (ex: production stricte Alembic-only), en miroir
exact du modele HeureTravail (app/models.py) et du style des autres tables
de la migration de base (7e066477f1a8).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd9d87b93c80b'
down_revision: Union[str, None] = '7e066477f1a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'heures_travail',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('chantier_id', sa.Integer(), nullable=False),
        sa.Column('membre_id', sa.Integer(), nullable=True),
        sa.Column('nom_intervenant', sa.String(), nullable=False),
        sa.Column('date_travail', sa.Date(), nullable=True),
        sa.Column('duree_heures', sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column('taux_horaire', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('note', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['chantier_id'], ['chantiers.id'], ),
        sa.ForeignKeyConstraint(['membre_id'], ['membres.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_heures_travail_chantier_id'), 'heures_travail', ['chantier_id'], unique=False)
    op.create_index(op.f('ix_heures_travail_id'), 'heures_travail', ['id'], unique=False)
    op.create_index(op.f('ix_heures_travail_membre_id'), 'heures_travail', ['membre_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_heures_travail_membre_id'), table_name='heures_travail')
    op.drop_index(op.f('ix_heures_travail_id'), table_name='heures_travail')
    op.drop_index(op.f('ix_heures_travail_chantier_id'), table_name='heures_travail')
    op.drop_table('heures_travail')
