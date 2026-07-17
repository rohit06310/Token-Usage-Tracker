"""
AlertSent ORM model.
Tracks alerts that have been sent to avoid duplicate notifications (deduplication).
"""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid
from sqlalchemy.sql import func

from app.models.base import Base, UUIDPrimaryKeyMixin


class AlertSent(UUIDPrimaryKeyMixin, Base):
    """
    Log of alerts dispatched.
    """
    __tablename__ = "ai_alerts_sent"

    provider_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("ai_providers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("ai_users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # 'tpm', 'rpm', 'rpd'
    threshold_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    provider: Mapped["Provider"] = relationship("Provider")  # noqa: F821

    def __repr__(self) -> str:
        return f"<AlertSent {self.alert_type} @ {self.threshold_percent}%>"
