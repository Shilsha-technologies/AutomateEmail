"""change_experience_to_string

Revision ID: 8c4dc07554f0
Revises: 6192b5e043fd
Create Date: 2026-05-08 11:55:37.567079

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8c4dc07554f0'
down_revision: Union[str, Sequence[str], None] = '6192b5e043fd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('attachments', 'experience',
               existing_type=sa.INTEGER(),
               type_=sa.String(),
               existing_nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('attachments', 'experience',
               existing_type=sa.String(),
               type_=sa.INTEGER(),
               existing_nullable=True)
