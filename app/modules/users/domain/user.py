from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID

from app.modules.users.domain.events import UserRegistered
from app.modules.users.domain.value_objects import (
    Authority,
    Email,
    HashedPassword,
    Nickname,
)
from app.shared.events import DomainEvent, EventRecorder


@dataclass
class User:
    """Pure domain entity — no SQLAlchemy, no Pydantic, no HTTP.

    Domain events raised during state transitions are collected on the
    aggregate via a composed `EventRecorder` (not inherited). The
    application layer drains them with `pull_events()` after a successful
    write.
    """

    id: UUID
    email: Email
    nickname: Nickname
    password_hash: HashedPassword
    authority: Authority = Authority.USER
    is_admin: bool = False
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    _events: EventRecorder = field(
        default_factory=EventRecorder, init=False, repr=False, compare=False
    )

    def pull_events(self) -> list[DomainEvent]:
        return self._events.pull()

    @classmethod
    def register(
        cls,
        *,
        user_id: UUID,
        email: Email,
        nickname: Nickname,
        password_hash: HashedPassword,
        occurred_at: datetime,
    ) -> "User":
        user = cls(
            id=user_id,
            email=email,
            nickname=nickname,
            password_hash=password_hash,
            authority=Authority.USER,
            is_admin=False,
            is_active=True,
        )
        user._events.record(
            UserRegistered(
                user_id=user.id,
                email=user.email.value,
                nickname=user.nickname.value,
                occurred_at=occurred_at,
            )
        )
        return user

    def disable(self) -> None:
        self.is_active = False

    def promote_to_admin(self) -> None:
        self.is_admin = True
        self.authority = Authority.ADMIN
