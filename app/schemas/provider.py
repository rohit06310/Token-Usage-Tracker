"""Pydantic schemas for Provider."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class ProviderBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120, examples=["OpenAI"])
    slug: str = Field(
        ...,
        min_length=1,
        max_length=60,
        pattern=r"^[a-z0-9_-]+$",
        examples=["openai"],
        description="URL-safe lowercase identifier used to look up the adapter.",
    )
    base_url: str | None = Field(None, examples=["https://api.openai.com/v1"])
    notes: str | None = Field(None, examples=["GPT-4 family — Tier 2 account"])


class ProviderCreate(ProviderBase):
    """Schema for creating a new provider."""
    pass


class ProviderUpdate(BaseModel):
    """Schema for partial updates to a provider."""
    name: str | None = Field(None, max_length=120)
    base_url: str | None = None
    notes: str | None = None


class ProviderRead(ProviderBase):
    """Schema for reading a provider from the API."""
    id: UUID
    confidence_level: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
