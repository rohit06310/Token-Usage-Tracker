"""Shared schema primitives."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class APIResponse(BaseModel):
    """Generic API envelope."""
    success: bool = True
    message: str = "OK"


class TimestampSchema(BaseModel):
    """Shared timestamp fields for read schemas."""
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
