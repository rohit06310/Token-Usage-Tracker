"""
UsageLog ORM model.
One row per LLM API call — the canonical record for cost/token tracking.
"""

import enum
import uuid
from decimal import Decimal

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB as PGJSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON, Uuid

# Use standard JSON on MySQL/SQLite, upgrade to JSONB on PostgreSQL
JsonColumn = JSON().with_variant(PGJSONB(), "postgresql")

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class CallStatus(str, enum.Enum):
    """Status of the LLM API call."""
    SUCCESS = "success"
    FAILED = "failed"


class UsageLog(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    A single LLM API call usage record.

    Columns
    -------
    id              UUID PK
    provider_id     FK → providers.id
    model           Model name, e.g. "gpt-4o", "claude-3-5-sonnet-20241022"
    tokens_in       Prompt / input token count
    tokens_out      Completion / output token count
    cost            Calculated USD cost (Decimal for precision)
    status          'success' or 'failed'
    project_tag     Arbitrary tag for grouping by project / feature
    raw_response    Full raw usage object from provider response (JSONB)
                    Stored so we can re-process if pricing changes.
                    On failure, contains {"error": "...", "_status": "failed"}
    created_at      When the call was made (auto-managed UTC)
    updated_at      Auto-managed UTC

    Indexes
    -------
    - provider_id (FK index)
    - created_at  (for time-range queries)
    - project_tag (for per-project aggregation)
    - status      (for filtering failures)
    """

    __tablename__ = "ai_usage_logs"

    provider_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("ai_providers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("ai_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        server_default="00000000-0000-0000-0000-000000000000",
    )
    model: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    tokens_in: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tokens_out: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=8),
        nullable=False,
        default=Decimal("0"),
        comment="Cost in USD with high precision to handle fractional cent costs.",
    )
    status: Mapped[str] = mapped_column(
        SAEnum(CallStatus, name="call_status_enum", create_constraint=True, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=CallStatus.SUCCESS,
        index=True,
        comment="Whether the API call succeeded or failed.",
    )
    project_tag: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        index=True,
        comment="Optional tag for grouping usage by project, feature, or team.",
    )
    raw_response: Mapped[dict | None] = mapped_column(
        JsonColumn,
        nullable=True,
        comment=(
            "Full raw usage payload from the provider. Stored for future reprocessing. "
            "On failed calls, contains {'error': '...', '_status': 'failed'}."
        ),
    )

    # Relationship
    provider: Mapped["Provider"] = relationship("Provider", back_populates="ai_usage_logs")  # noqa: F821
    user: Mapped["User"] = relationship("User", back_populates="ai_usage_logs")  # noqa: F821

    @property
    def total_tokens(self) -> int:
        return self.tokens_in + self.tokens_out

    @property
    def is_success(self) -> bool:
        return self.status == CallStatus.SUCCESS

    def __repr__(self) -> str:
        return (
            f"<UsageLog id={self.id!s:.8} model={self.model!r} "
            f"status={self.status} tokens=({self.tokens_in}+{self.tokens_out}) cost=${self.cost}>"
        )
