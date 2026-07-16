"""
ReconciliationResult ORM model.
Stores the outcome of comparing self-logged usage vs. provider-reported usage.
"""

import uuid
from decimal import Decimal
from datetime import datetime

from sqlalchemy import String, Enum, Integer, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid
from sqlalchemy.sql import func

from app.models.base import Base, UUIDPrimaryKeyMixin


class ReconciliationResult(UUIDPrimaryKeyMixin, Base):
    """
    Stores reconciliation results for a provider over a specific period.
    """
    __tablename__ = "reconciliation_results"

    provider_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("providers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    self_logged_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    provider_reported_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    difference: Mapped[int] = mapped_column(Integer, nullable=False)
    percent_diff: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    
    status: Mapped[str] = mapped_column(
        Enum("matched", "mismatched", "no_official_data", name="reconciliation_status_enum", create_type=False),
        nullable=False,
        index=True
    )
    
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    provider: Mapped["Provider"] = relationship("Provider")  # noqa: F821

    def __repr__(self) -> str:
        return f"<ReconciliationResult {self.status} diff={self.percent_diff}%>"
