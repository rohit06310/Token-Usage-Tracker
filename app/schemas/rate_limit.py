"""Pydantic schemas for RateLimit."""

from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RateLimitCreate(BaseModel):
    provider_id: UUID
    tier_name: str = Field(..., max_length=100, examples=["Tier 1"])
    rpm: int | None = Field(None, ge=0, description="Requests per minute")
    tpm: int | None = Field(None, ge=0, description="Tokens per minute")
    rpd: int | None = Field(None, ge=0, description="Requests per day")
    effective_date: date


class RateLimitRead(BaseModel):
    id: UUID
    provider_id: UUID
    tier_name: str
    rpm: int | None
    tpm: int | None
    rpd: int | None
    effective_date: date
    created_at: str
    updated_at: str

    model_config = ConfigDict(from_attributes=True)
