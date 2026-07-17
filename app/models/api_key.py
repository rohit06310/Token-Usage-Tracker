"""
ApiKey ORM model.
Stores ENCRYPTED provider API keys — plaintext is NEVER persisted.
"""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ApiKey(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    An encrypted API key belonging to a Provider.

    Columns
    -------
    id              UUID PK
    provider_id     FK → providers.id
    encrypted_key   Fernet-encrypted ciphertext (never plaintext)
    label           Human-readable label, e.g. "prod key", "dev key"
    is_active       Soft-disable a key without deleting it
    created_at / updated_at  auto-managed timestamps

    The `encrypted_key` field stores the output of FernetEncryption.encrypt().
    To use the key, call FernetEncryption.decrypt(api_key_row.encrypted_key).
    """

    __tablename__ = "ai_api_keys"

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
    encrypted_key: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Fernet-encrypted provider API key. Never store plaintext here.",
    )
    label: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        default="default",
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Relationship
    provider: Mapped["Provider"] = relationship("Provider", back_populates="ai_api_keys")  # noqa: F821
    user: Mapped["User"] = relationship("User", back_populates="ai_api_keys")  # noqa: F821

    def __repr__(self) -> str:
        return f"<ApiKey id={self.id!s:.8} label={self.label!r} provider_id={self.provider_id!s:.8} user_id={self.user_id!s:.8}>"
