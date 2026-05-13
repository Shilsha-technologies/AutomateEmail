"""merge migration branches

Revision ID: f4ee2b697b04
Revises: 9076afcac9f0, af11d3b02667
Create Date: 2026-05-13 09:50:30.893106

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f4ee2b697b04'
down_revision: Union[str, Sequence[str], None] = ('9076afcac9f0', 'af11d3b02667')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
