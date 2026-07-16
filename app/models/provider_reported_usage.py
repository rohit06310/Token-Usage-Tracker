"""
ProviderReportedUsage ORM model.
Stores usage/billing data fetched directly from provider APIs.
Used for reconciliation against our locally tracked usage_logs.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ProviderReportedUsage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    A single period of usage as reported by the provider's billing API.

    This is the "ground truth" from the provider side — used in Phase 3
    to reconcile against our locally tracked usage_logs.

    Columns
    -------
    id              UUID PK
    provider_id     FK → providers.id
    period_start    Start of the billing period (UTC, inclusive)
    period_end      End of the billing period (UTC, inclusive)
    total_tokens    Total tokens reported by provider for the period
    total_cost      Total cost reported by provider for the period (USD)
    fetched_at      When we fetched this data from the provider API
    source          Which provider API endpoint was queried
    raw_payload     Full raw JSON response from provider billing API
    created_at / updated_at  auto-managed timestamps
    """

    __tablename__ = "provider_reported_usage"

    provider_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("providers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="Start of the usage period (UTC).",
    )
    period_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="End of the usage period (UTC).",
    )
    total_tokens: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Total tokens for the period as reported by the provider.",
    )
    total_cost: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=18, scale=8),
        nullable=True,
        comment="Total cost (USD) as reported by the provider.",
    )
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="When this record was fetched from the provider API.",
    )
    source: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        default="api",
        comment="Which endpoint/method was used to fetch this data.",
    )

    # Relationship
    provider: Mapped["Provider"] = relationship(  # noqa: F821
        "Provider", back_populates="reported_usage"
    )

    def __repr__(self) -> str:
        return (
            f"<ProviderReportedUsage id={self.id!s:.8} "
            f"provider={self.provider_id!s:.8} "
            f"period={self.period_start.date()}→{self.period_end.date()} "
            f"cost=${self.total_cost}>"
        )
