"""add sync scope to sync jobs

Revision ID: 20260602_0002
Revises: 20260602_0001
Create Date: 2026-06-02 00:00:02

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260602_0002"
down_revision: Union[str, Sequence[str], None] = "20260602_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "sync_jobs",
        sa.Column(
            "sync_scope",
            sa.String(),
            nullable=False,
            server_default="days",
        ),
    )
    op.create_index(op.f("ix_sync_jobs_sync_scope"), "sync_jobs", ["sync_scope"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_sync_jobs_sync_scope"), table_name="sync_jobs")
    op.drop_column("sync_jobs", "sync_scope")
