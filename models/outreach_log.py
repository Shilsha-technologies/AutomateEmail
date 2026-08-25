from sqlalchemy import Boolean, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func

from database.db import Base


class OutreachLog(Base):
    __tablename__ = "outreach_logs"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(String, nullable=False, index=True)
    hr_user_id = Column(Integer, ForeignKey("hr_users.id"), nullable=False, index=True)
    source_email_id = Column(Integer, ForeignKey("emails.id"), nullable=True, index=True)

    provider = Column(String, nullable=False)
    recipient_email = Column(String, nullable=False, index=True)
    candidate_name = Column(String, nullable=True)
    job_role = Column(String, nullable=True)

    subject = Column(Text, nullable=True)
    body = Column(Text, nullable=True)

    status = Column(String, nullable=False, index=True)
    error_message = Column(Text, nullable=True)
    provider_message_id = Column(String, nullable=True)

    # Whether this attempt was requested as a threaded reply, and whether it
    # actually went out inside the candidate's original thread. `is_reply`
    # reflects the caller's intent; `threaded` reflects the real outcome
    # (False if we had to silently fall back to a new email because the
    # source message had no thread metadata).
    is_reply = Column(Boolean, nullable=False, server_default="false")
    threaded = Column(Boolean, nullable=False, server_default="false")

    attempted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)