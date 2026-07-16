"""Pydantic schemas for UsageLog."""

from decimal import Decimal
from typing import Any
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UsageLogCreate(BaseModel):
    """Schema for inserting a usage log (used internally by adapters)."""
    provider_id: UUID
    model: str = Field(..., max_length=200, examples=["gpt-4o"])
    tokens_in: int = Field(default=0, ge=0)
    tokens_out: int = Field(default=0, ge=0)
    cost: Decimal = Field(default=Decimal("0"), ge=0)
    project_tag: str | None = Field(None, max_length=200)
    raw_response: dict[str, Any] | None = None


class UsageLogRead(BaseModel):
    """Schema for reading a usage log from the API."""
    id: UUID
    provider_id: UUID
    model: str
    tokens_in: int
    tokens_out: int
    total_tokens: int
    cost: Decimal
    project_tag: str | None
    raw_response: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UsageLogPaginated(BaseModel):
    """Schema for a paginated list of usage logs."""
    items: list[UsageLogRead]
    total: int


class UsageSummary(BaseModel):
    """Aggregated usage statistics."""
    total_calls: int
    total_tokens_in: int
    total_tokens_out: int
    total_tokens: int
    total_cost: Decimal
    by_model: dict[str, dict[str, Any]] = Field(default_factory=dict)
    by_project: dict[str, dict[str, Any]] = Field(default_factory=dict)
