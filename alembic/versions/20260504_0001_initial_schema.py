"""initial schema
 
Revision ID: 20260504_0001
Revises:
Create Date: 2026-05-04 00:00:01
 
"""
 
from typing import Sequence, Union
 
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
 
 
# revision identifiers, used by Alembic.
revision: str = "20260504_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None
 
 
def upgrade() -> None:
    op.create_table(
        "candidates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("email", sa.Text(), nullable=True),
        sa.Column("phone", sa.Text(), nullable=True),
        sa.Column("linkedin", sa.Text(), nullable=True),
        sa.Column("github", sa.Text(), nullable=True),
        sa.Column("skills", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("experience", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("education", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("projects", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("certifications", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("source", sa.Text(), nullable=True),
        sa.Column("email_id", sa.Text(), nullable=True),
        sa.Column("email_date", sa.Text(), nullable=True),
        sa.Column("email_subject", sa.Text(), nullable=True),
        sa.Column("sender_email", sa.Text(), nullable=True),
        sa.Column("provider", sa.Text(), nullable=True),
        sa.Column("attachment_name", sa.Text(), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("resume_url", sa.Text(), nullable=True),
        sa.Column("created_at", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_candidates_id"), "candidates", ["id"], unique=False)
 
    op.create_table(
        "employees",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password", sa.String(), nullable=False),
        sa.Column("mobile", sa.String(), nullable=False),
        sa.Column("gender", sa.String(), nullable=True),
        sa.Column("user_type", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_employees_email"), "employees", ["email"], unique=True)
    op.create_index(op.f("ix_employees_id"), "employees", ["id"], unique=False)
    op.create_index(op.f("ix_employees_mobile"), "employees", ["mobile"], unique=True)
 
    op.create_table(
        "resume_analysis",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("candidate_name", sa.String(length=255), nullable=False),
        sa.Column("candidate_email", sa.String(length=255), nullable=True),
        sa.Column("domain", sa.String(length=100), nullable=False),
        sa.Column("skills", sa.JSON(), nullable=False),
        sa.Column("level", sa.String(length=50), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("summary", sa.String(length=512), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("folder_path", sa.String(length=255), nullable=False),
        sa.Column("drive_file_id", sa.String(length=255), nullable=True),
        sa.Column("drive_link", sa.String(length=512), nullable=True),
        sa.Column("source", sa.String(length=100), nullable=True),
        sa.Column("provider", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_resume_analysis_id"), "resume_analysis", ["id"], unique=False)
 
    op.create_table(
        "token_blacklist",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(), nullable=False),
        sa.Column("blacklisted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_token_blacklist_id"), "token_blacklist", ["id"], unique=False)
    op.create_index(op.f("ix_token_blacklist_token"), "token_blacklist", ["token"], unique=True)
 
    op.create_table(
        "hr_users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("access_token", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("employee_id", "provider", "email", name="uix_hr_user_employee_provider_email"),
    )
    op.create_index(op.f("ix_hr_users_email"), "hr_users", ["email"], unique=False)
    op.create_index(op.f("ix_hr_users_employee_id"), "hr_users", ["employee_id"], unique=False)
    op.create_index(op.f("ix_hr_users_id"), "hr_users", ["id"], unique=False)
 
    op.create_table(
        "email_templates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("template_name", sa.String(), nullable=False),
        sa.Column("template_data", sa.Text(), nullable=False),
        sa.Column("subject", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_email_templates_employee_id"), "email_templates", ["employee_id"], unique=False)
    op.create_index(op.f("ix_email_templates_id"), "email_templates", ["id"], unique=False)
 
    op.create_table(
        "signatures",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("signature_name", sa.String(), nullable=False),
        sa.Column("signature_data", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_signatures_employee_id"), "signatures", ["employee_id"], unique=False)
    op.create_index(op.f("ix_signatures_id"), "signatures", ["id"], unique=False)
 
    op.create_table(
        "emails",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("hr_user_id", sa.Integer(), nullable=True),
        sa.Column("email_id", sa.String(), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("candidate_name", sa.String(), nullable=True),
        sa.Column("candidate_email", sa.String(), nullable=True),
        sa.Column("subject", sa.String(), nullable=True),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("date", sa.String(), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("has_attachments", sa.Boolean(), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=True),
        sa.Column("is_job_application", sa.Boolean(), nullable=True),
        sa.Column("job_position", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["hr_user_id"], ["hr_users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("hr_user_id", "email_id", name="uix_email_hr_user_email_id"),
    )
    op.create_index(op.f("ix_emails_candidate_email"), "emails", ["candidate_email"], unique=False)
    op.create_index(op.f("ix_emails_email_id"), "emails", ["email_id"], unique=False)
    op.create_index(op.f("ix_emails_hr_user_id"), "emails", ["hr_user_id"], unique=False)
    op.create_index(op.f("ix_emails_id"), "emails", ["id"], unique=False)
    op.create_index(op.f("ix_emails_received_at"), "emails", ["received_at"], unique=False)
 
    op.create_table(
        "attachments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email_id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("file_path", sa.String(), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("file_type", sa.String(), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("linkedin", sa.String(), nullable=True),
        sa.Column("github", sa.String(), nullable=True),
        sa.Column("skills", sa.Text(), nullable=True),
        sa.Column("experience", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["email_id"], ["emails.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_attachments_id"), "attachments", ["id"], unique=False)
 
    op.create_table(
        "attachment_activity",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("attachment_id", sa.Integer(), nullable=False),
        sa.Column("hr_user_id", sa.Integer(), nullable=False),
        sa.Column("viewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("downloaded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["attachment_id"], ["attachments.id"]),
        sa.ForeignKeyConstraint(["hr_user_id"], ["hr_users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("attachment_id", "hr_user_id", name="uix_attachment_activity_hr_user"),
    )
    op.create_index(op.f("ix_attachment_activity_attachment_id"), "attachment_activity", ["attachment_id"], unique=False)
    op.create_index(op.f("ix_attachment_activity_hr_user_id"), "attachment_activity", ["hr_user_id"], unique=False)
    op.create_index(op.f("ix_attachment_activity_id"), "attachment_activity", ["id"], unique=False)
 
 
def downgrade() -> None:
    op.drop_index(op.f("ix_attachment_activity_id"), table_name="attachment_activity")
    op.drop_index(op.f("ix_attachment_activity_hr_user_id"), table_name="attachment_activity")
    op.drop_index(op.f("ix_attachment_activity_attachment_id"), table_name="attachment_activity")
    op.drop_table("attachment_activity")
 
    op.drop_index(op.f("ix_attachments_id"), table_name="attachments")
    op.drop_table("attachments")
 
    op.drop_index(op.f("ix_emails_received_at"), table_name="emails")
    op.drop_index(op.f("ix_emails_id"), table_name="emails")
    op.drop_index(op.f("ix_emails_hr_user_id"), table_name="emails")
    op.drop_index(op.f("ix_emails_email_id"), table_name="emails")
    op.drop_index(op.f("ix_emails_candidate_email"), table_name="emails")
    op.drop_table("emails")
 
    op.drop_index(op.f("ix_signatures_id"), table_name="signatures")
    op.drop_index(op.f("ix_signatures_employee_id"), table_name="signatures")
    op.drop_table("signatures")
 
    op.drop_index(op.f("ix_email_templates_id"), table_name="email_templates")
    op.drop_index(op.f("ix_email_templates_employee_id"), table_name="email_templates")
    op.drop_table("email_templates")
 
    op.drop_index(op.f("ix_hr_users_id"), table_name="hr_users")
    op.drop_index(op.f("ix_hr_users_employee_id"), table_name="hr_users")
    op.drop_index(op.f("ix_hr_users_email"), table_name="hr_users")
    op.drop_table("hr_users")
 
    op.drop_index(op.f("ix_token_blacklist_token"), table_name="token_blacklist")
    op.drop_index(op.f("ix_token_blacklist_id"), table_name="token_blacklist")
    op.drop_table("token_blacklist")
 
    op.drop_index(op.f("ix_resume_analysis_id"), table_name="resume_analysis")
    op.drop_table("resume_analysis")
 
    op.drop_index(op.f("ix_employees_mobile"), table_name="employees")
    op.drop_index(op.f("ix_employees_id"), table_name="employees")
    op.drop_index(op.f("ix_employees_email"), table_name="employees")
    op.drop_table("employees")
 
    op.drop_index(op.f("ix_candidates_id"), table_name="candidates")
    op.drop_table("candidates")
 