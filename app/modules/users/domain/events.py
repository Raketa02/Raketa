from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class UserRegistered:
    user_id: UUID
    email: str
    nickname: str
    password_hash: str
    authority: str
    is_admin: bool
    is_active: bool
    occurred_at: datetime


@dataclass(frozen=True)
class UserDisabled:
    user_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class UserPromotedToAdmin:
    user_id: UUID
    occurred_at: datetime
