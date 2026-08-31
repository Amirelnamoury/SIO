"""design preferences et candidate site vitrine (configurateur admin, Lot 4)

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-08-31 03:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Nullables et sans server_default volontairement : un site existant n'a
    # ni preference ni alternative en cours, et n'en a pas besoin pour
    # continuer a fonctionner (voir app/models.py::SiteVitrine). Aucune
    # donnee retroactivement inventee.
    op.add_column('sites_vitrines', sa.Column('design_preferences', sa.JSON(), nullable=True))
    op.add_column('sites_vitrines', sa.Column('candidate_design_profile', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('sites_vitrines', 'candidate_design_profile')
    op.drop_column('sites_vitrines', 'design_preferences')
