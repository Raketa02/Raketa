from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from app.modules.users.domain.value_objects import (
    Authority,
    Email,
    HashedPassword,
    Nickname,
)


@dataclass
class User:
    """Pure domain entity — no SQLAlchemy, no Pydantic, no HTTP."""

    id: UUID
    email: Email
    nickname: Nickname
    password_hash: HashedPassword
    authority: Authority = Authority.USER
    is_admin: bool = False
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def disable(self) -> None:
        self.is_active = False

    def promote_to_admin(self) -> None:
        self.is_admin = True
        self.authority = Authority.ADMIN
