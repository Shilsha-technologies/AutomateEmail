"""add sync jobs

Revision ID: 20260602_0001
Revises: f4ee2b697b04
Create Date: 2026-06-02 00:00:01

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260602_0001"
down_revision: Union[str, Sequence[str], None] = "f4ee2b697b04"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sync_jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("hr_user_id", sa.Integer(), nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=True),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("days", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("synced_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"]),
        sa.ForeignKeyConstraint(["hr_user_id"], ["hr_users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sync_jobs_employee_id"), "sync_jobs", ["employee_id"], unique=False)
    op.create_index(op.f("ix_sync_jobs_hr_user_id"), "sync_jobs", ["hr_user_id"], unique=False)
    op.create_index(op.f("ix_sync_jobs_id"), "sync_jobs", ["id"], unique=False)
    op.create_index(op.f("ix_sync_jobs_provider"), "sync_jobs", ["provider"], unique=False)
    op.create_index(op.f("ix_sync_jobs_status"), "sync_jobs", ["status"], unique=False)

    op.add_column("emails", sa.Column("sync_job_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_emails_sync_job_id_sync_jobs", "emails", "sync_jobs", ["sync_job_id"], ["id"])
    op.create_index(op.f("ix_emails_sync_job_id"), "emails", ["sync_job_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_emails_sync_job_id"), table_name="emails")
    op.drop_constraint("fk_emails_sync_job_id_sync_jobs", "emails", type_="foreignkey")
    op.drop_column("emails", "sync_job_id")

    op.drop_index(op.f("ix_sync_jobs_status"), table_name="sync_jobs")
    op.drop_index(op.f("ix_sync_jobs_provider"), table_name="sync_jobs")
    op.drop_index(op.f("ix_sync_jobs_id"), table_name="sync_jobs")
    op.drop_index(op.f("ix_sync_jobs_hr_user_id"), table_name="sync_jobs")
    op.drop_index(op.f("ix_sync_jobs_employee_id"), table_name="sync_jobs")
    op.drop_table("sync_jobs")
