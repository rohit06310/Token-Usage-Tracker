"""
JobRun ORM model.
Tracks execution of background scheduled jobs to provide visibility into failures.
"""

import uuid
from datetime import datetime

from sqlalchemy import String, Enum, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import Base, UUIDPrimaryKeyMixin


class JobRun(UUIDPrimaryKeyMixin, Base):
    """
    Log of scheduled job executions.
    """
    __tablename__ = "ai_job_runs"

    job_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        Enum("success", "failed", "running", name="job_status_enum", create_type=False),
        nullable=False,
        index=True,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<JobRun {self.job_name} {self.status}>"
