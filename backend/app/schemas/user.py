"""User schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal, TypedDict

from pydantic import BaseModel, ConfigDict, Field

PreferredLanguage = Literal["en", "ne", "hi"]
Role = Literal["citizen", "human_helper", "admin"]


class UserPublic(BaseModel):
    """Safe public representation of a user (never contains password data)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: str
    phone: str
    role: Role
    preferred_language: PreferredLanguage
    created_at: datetime


class UserUpdate(BaseModel):
    """Editable user profile fields."""

    preferred_language: PreferredLanguage | None = None
    name: str | None = Field(default=None, min_length=2, max_length=100)


class UserContext(TypedDict):
    """Authenticated user context resolved from the JWT."""

    id: str
    name: str
    email: str
    role: str
    preferred_language: str
