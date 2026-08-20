"""Request/response schemas for authentication endpoints (Module 16)."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from .. import db as _db  # noqa: F401  (imported first for its sys.path side effect —
# `database` isn't importable until this runs; see app/db.py's docstring)
from database.models import UserRole


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    role: UserRole
    created_at: datetime

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=8, max_length=255)
    role: UserRole = UserRole.INVESTIGATOR


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=255)
