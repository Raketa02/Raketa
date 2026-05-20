from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, validator

from app.modules.users.domain.user import User


class UserCreateRequest(BaseModel):
    email: EmailStr
    password1: str = Field(..., min_length=8, max_length=128)
    password2: str = Field(..., min_length=8, max_length=128)
    nickname: str = Field(
        ..., min_length=2, max_length=64, regex=r"^[A-Za-z0-9_.-]+$"
    )

    @validator("password2")
    def _passwords_match(cls, v: str, values) -> str:
        if "password1" in values and v != values["password1"]:
            raise ValueError("passwords do not match")
        return v


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    nickname: str
    authority: str
    is_admin: bool
    is_active: bool
    created_at: Optional[datetime] = None

    @classmethod
    def from_domain(cls, user: User) -> "UserResponse":
        return cls(
            id=user.id,
            email=user.email.value,
            nickname=user.nickname.value,
            authority=user.authority.value,
            is_admin=user.is_admin,
            is_active=user.is_active,
            created_at=user.created_at,
        )
