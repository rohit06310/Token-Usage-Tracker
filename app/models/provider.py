"""
Provider ORM model.
Represents an LLM provider (OpenAI, Anthropic, Groq, Gemini, etc.).
"""

import uuid

from sqlalchemy import String, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Provider(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    A registered LLM provider.

    Columns
    -------
    id          UUID PK (auto-generated)
    name        Human-readable name, e.g. "OpenAI", "Anthropic"
    slug        URL-safe identifier, e.g. "openai", "anthropic" — used to
                look up the correct adapter class at runtime
    base_url    The provider's API base URL (informational / override)
    notes       Free-form notes (pricing tier, contact, etc.)
    created_at  Auto-managed UTC timestamp
    updated_at  Auto-managed UTC timestamp
    """

    __tablename__ = "providers"

    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(60), nullable=False, unique=True, index=True)
    base_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    confidence_level: Mapped[str] = mapped_column(
        Enum("verified", "self_logged_only", "unreliable", name="confidence_level_enum", create_type=False),
        nullable=False,
        server_default="self_logged_only",
    )

    # Relationships (back-populated by child models)
    api_keys: Mapped[list["ApiKey"]] = relationship(  # noqa: F821
        "ApiKey", back_populates="provider", cascade="all, delete-orphan"
    )
    usage_logs: Mapped[list["UsageLog"]] = relationship(  # noqa: F821
        "UsageLog", back_populates="provider", cascade="all, delete-orphan"
    )
    rate_limits: Mapped[list["RateLimit"]] = relationship(  # noqa: F821
        "RateLimit", back_populates="provider", cascade="all, delete-orphan"
    )
    reported_usage: Mapped[list["ProviderReportedUsage"]] = relationship(  # noqa: F821
        "ProviderReportedUsage", back_populates="provider", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Provider id={self.id!s:.8} name={self.name!r}>"
