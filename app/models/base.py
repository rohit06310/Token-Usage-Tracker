"""
Shared SQLAlchemy declarative base and reusable mixins.
All ORM models should inherit from Base (and optionally TimestampMixin).
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, func, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import Uuid  # SQLAlchemy 2.0 cross-dialect UUID


class Base(DeclarativeBase):
    """Project-wide SQLAlchemy declarative base."""
    pass


class TimestampMixin:
    """
    Adds `created_at` and `updated_at` columns to any model.
    Both are timezone-aware UTC timestamps managed by the DB server.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class UUIDPrimaryKeyMixin:
    """
    Adds a UUID primary key to any model.

    Uses sqlalchemy.types.Uuid (SQLAlchemy 2.0+) which is cross-dialect:
    - PostgreSQL: stores as native UUID
    - SQLite:     stores as VARCHAR(32) (for tests)

    Python-side default (uuid.uuid4) fires when inserting without an explicit id.
    """

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
