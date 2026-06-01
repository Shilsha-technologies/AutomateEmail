"""drop attachment_views

Revision ID: af11d3b02667
Revises: 20260505_0002
Create Date: 2026-05-12 09:33:26.968813

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'af11d3b02667'
down_revision: Union[str, Sequence[str], None] = '20260505_0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute('DROP TABLE IF EXISTS attachment_views CASCADE')


def downgrade() -> None:
    """Downgrade schema."""
    op.create_table(
        'attachment_views',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('attachment_id', sa.Integer(), nullable=False),
        sa.Column('hr_user_id', sa.Integer(), nullable=False),
        sa.Column('viewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['attachment_id'], ['attachments.id']),
        sa.ForeignKeyConstraint(['hr_user_id'], ['hr_users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('attachment_id', 'hr_user_id', name='uix_attachment_hr_user'),
    )
    op.create_index(op.f('ix_attachment_views_attachment_id'), 'attachment_views', ['attachment_id'], unique=False)
    op.create_index(op.f('ix_attachment_views_hr_user_id'), 'attachment_views', ['hr_user_id'], unique=False)
    op.create_index(op.f('ix_attachment_views_id'), 'attachment_views', ['id'], unique=False)
