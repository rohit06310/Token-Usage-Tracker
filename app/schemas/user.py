import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: uuid.UUID
    preferred_currency: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    preferred_currency: str | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
