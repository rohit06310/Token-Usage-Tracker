"""
User ORM model.
Represents a dashboard user who can log in, generate API keys, and view their usage logs.
"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    Dashboard User.

    Columns
    -------
    id              UUID PK
    email           User's email (unique, indexed)
    hashed_password Passlib bcrypt hash
    created_at / updated_at  auto-managed timestamps
    """

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    preferred_currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)

    # Relationships
    api_keys: Mapped[list["ApiKey"]] = relationship(  # noqa: F821
        "ApiKey", back_populates="user", cascade="all, delete-orphan"
    )
    usage_logs: Mapped[list["UsageLog"]] = relationship(  # noqa: F821
        "UsageLog", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id!s:.8} email={self.email!r}>"
