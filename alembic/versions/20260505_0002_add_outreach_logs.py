"""add outreach logs table

Revision ID: 20260505_0002
Revises: 20260504_0001
Create Date: 2026-05-05 00:00:02
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260505_0002"
down_revision: Union[str, Sequence[str], None] = "20260504_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "outreach_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("batch_id", sa.String(), nullable=False),
        sa.Column("hr_user_id", sa.Integer(), nullable=False),
        sa.Column("source_email_id", sa.Integer(), nullable=True),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("recipient_email", sa.String(), nullable=False),
        sa.Column("candidate_name", sa.String(), nullable=True),
        sa.Column("job_role", sa.String(), nullable=True),
        sa.Column("subject", sa.Text(), nullable=True),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("provider_message_id", sa.String(), nullable=True),
        sa.Column("attempted_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["hr_user_id"], ["hr_users.id"]),
        sa.ForeignKeyConstraint(["source_email_id"], ["emails.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(op.f("ix_outreach_logs_id"), "outreach_logs", ["id"], unique=False)
    op.create_index(op.f("ix_outreach_logs_batch_id"), "outreach_logs", ["batch_id"], unique=False)
    op.create_index(op.f("ix_outreach_logs_hr_user_id"), "outreach_logs", ["hr_user_id"], unique=False)
    op.create_index(op.f("ix_outreach_logs_source_email_id"), "outreach_logs", ["source_email_id"], unique=False)
    op.create_index(op.f("ix_outreach_logs_recipient_email"), "outreach_logs", ["recipient_email"], unique=False)
    op.create_index(op.f("ix_outreach_logs_status"), "outreach_logs", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_outreach_logs_status"), table_name="outreach_logs")
    op.drop_index(op.f("ix_outreach_logs_recipient_email"), table_name="outreach_logs")
    op.drop_index(op.f("ix_outreach_logs_source_email_id"), table_name="outreach_logs")
    op.drop_index(op.f("ix_outreach_logs_hr_user_id"), table_name="outreach_logs")
    op.drop_index(op.f("ix_outreach_logs_batch_id"), table_name="outreach_logs")
    op.drop_index(op.f("ix_outreach_logs_id"), table_name="outreach_logs")
    op.drop_table("outreach_logs")
