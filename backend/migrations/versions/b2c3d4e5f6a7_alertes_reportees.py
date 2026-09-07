"""alertes calculees reportees a plus tard

Le centre de notifications melange deux natures : les evenements persistants
(table `notifications`, qu'on peut marquer lus) et les alertes metier
recalculees a chaque appel - devis a relancer, facture impayee, conformite qui
expire. Ces dernieres n'ont pas d'identifiant propre : rien ne permettait de
dire « je m'en occupe jeudi, ne me le remontre pas d'ici la ».

Cette table porte ce report. Elle n'efface rien : la facture reste en retard et
l'alerte reparait le jour dit.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "alertes_reportees",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("artisan_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("reference_id", sa.Integer(), nullable=False),
        sa.Column("jusqu_au", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["artisan_id"], ["artisans.id"]),
        sa.PrimaryKeyConstraint("id"),
        # L'identite d'une alerte calculee, c'est son type et la piece visee :
        # la reporter deux fois deplace l'echeance, elle ne cree pas une
        # seconde ligne.
        sa.UniqueConstraint("artisan_id", "type", "reference_id", name="uq_alerte_reportee_artisan_type_reference"),
    )
    op.create_index(op.f("ix_alertes_reportees_id"), "alertes_reportees", ["id"])
    op.create_index(op.f("ix_alertes_reportees_artisan_id"), "alertes_reportees", ["artisan_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_alertes_reportees_artisan_id"), table_name="alertes_reportees")
    op.drop_index(op.f("ix_alertes_reportees_id"), table_name="alertes_reportees")
    op.drop_table("alertes_reportees")
