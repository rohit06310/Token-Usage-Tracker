"""
RateLimit ORM model.
Records the rate-limit tiers for each provider (can change over time).
"""

import uuid
from datetime import date

from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Integer, String, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class RateLimit(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    A provider's rate-limit tier (point-in-time record).

    Multiple rows per provider are allowed — use effective_date to track
    tier changes over time. The latest row (by effective_date) is the active one.

    Columns
    -------
    id              UUID PK
    provider_id     FK → providers.id
    tier_name       e.g. "Tier 1", "Free", "Enterprise"
    rpm             Requests per minute
    tpm             Tokens per minute
    rpd             Requests per day
    effective_date  The date from which this tier applies
    created_at / updated_at  auto-managed timestamps
    """

    __tablename__ = "ai_rate_limits"

    provider_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("ai_providers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tier_name: Mapped[str] = mapped_column(String(100), nullable=False)
    rpm: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Requests per minute"
    )
    tpm: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Tokens per minute"
    )
    rpd: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Requests per day"
    )
    budget_usd: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 4), nullable=True, comment="Max dollar spend per month"
    )
    effective_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="The date from which this rate limit tier is effective.",
    )

    # Relationship
    provider: Mapped["Provider"] = relationship("Provider", back_populates="rate_limits")  # noqa: F821

    def __repr__(self) -> str:
        return (
            f"<RateLimit id={self.id!s:.8} provider={self.provider_id!s:.8} "
            f"tier={self.tier_name!r} rpm={self.rpm} effective={self.effective_date}>"
        )
