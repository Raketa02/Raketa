import re
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, validator

_PASSWORD_RE = re.compile(r"^(?=.*[A-Za-z])(?=.*\d).{8,128}$")


class UserCreateRequest(BaseModel):
    email: EmailStr
    password1: str = Field(..., min_length=8, max_length=128)
    password2: str = Field(..., min_length=8, max_length=128)
    nickname: str = Field(..., min_length=2, max_length=64, regex=r"^[A-Za-z0-9_.-]+$")

    @validator("password1")
    def _password_strength(cls, v: str) -> str:
        if not _PASSWORD_RE.match(v):
            raise ValueError(
                "password must be 8-128 chars with at least one letter and one digit"
            )
        return v

    @validator("password2")
    def _passwords_match(cls, v: str, values) -> str:
        if "password1" in values and v != values["password1"]:
            raise ValueError("passwords do not match")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    nickname: str
    authority: str
    is_admin: bool
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
