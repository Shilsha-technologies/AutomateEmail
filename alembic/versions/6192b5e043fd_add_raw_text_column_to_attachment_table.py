"""add raw_text column to attachment table

Revision ID: 6192b5e043fd
Revises: 20260505_0002
Create Date: 2026-05-08
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '6192b5e043fd'
down_revision = '20260505_0002'
branch_labels = None
depends_on = None


def upgrade():

    # Add email column
    op.add_column(
        'attachments',
        sa.Column('email', sa.String(), nullable=True)
    )

    # Add raw_text column
    op.add_column(
        'attachments',
        sa.Column('raw_text', sa.Text(), nullable=True)
    )

    # Convert experience column from VARCHAR to INTEGER
    op.execute("""
        ALTER TABLE attachments
        ALTER COLUMN experience
        TYPE INTEGER
        USING NULLIF(
            regexp_replace(experience, '[^0-9]', '', 'g'),
            ''
        )::integer
    """)


def downgrade():

    # Convert INTEGER back to VARCHAR
    op.execute("""
        ALTER TABLE attachments
        ALTER COLUMN experience
        TYPE VARCHAR
    """)

    # Remove columns
    op.drop_column('attachments', 'raw_text')
    op.drop_column('attachments', 'email')