"""Pydantic schemas for ApiKey."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ApiKeyCreate(BaseModel):
    """
    Schema for creating a new API key entry.
    The `raw_key` is the plaintext key — it will be encrypted before storage.
    It is ONLY present in the request body, never in responses.
    """
    provider_id: UUID
    raw_key: str = Field(
        ...,
        min_length=8,
        description="The plaintext provider API key. Will be encrypted at rest.",
    )
    label: str = Field(default="default", max_length=200)


class ApiKeyRead(BaseModel):
    """
    Schema for reading an API key entry from the API.
    The encrypted key is NEVER returned — only metadata.
    """
    id: UUID
    provider_id: UUID
    label: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
