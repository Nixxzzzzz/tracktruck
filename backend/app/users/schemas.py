"""
Pydantic v2 Schemas for Users and Roles.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    role_id: str = Field(..., description="Role identifier")
    description: str = Field(..., description="Role scope description")


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=128)
    phone_number: str | None = Field(default=None, max_length=32)
    role_id: str = Field(..., description="Assigned role identifier")


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Plaintext password")


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    username: str
    email: str
    full_name: str
    phone_number: str | None
    role_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
