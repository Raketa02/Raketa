from __future__ import annotations

from typing import Optional, Protocol, runtime_checkable
from uuid import UUID

from app.modules.users.domain.user import User


@runtime_checkable
class UserRepository(Protocol):
    async def get_by_id(self, user_id: UUID) -> Optional[User]: ...
    async def get_by_email(self, email: str) -> Optional[User]: ...
    async def get_by_nickname(self, nickname: str) -> Optional[User]: ...
    async def add(self, user: User) -> User: ...