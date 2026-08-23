from __future__ import annotations

from datetime import datetime
from typing import Optional, Protocol, Sequence, runtime_checkable
from uuid import UUID

from app.modules.users.domain.events import UserRegistered
from app.modules.users.domain.user import User


@runtime_checkable
class UserRepository(Protocol):
    async def get_by_id(self, user_id: UUID) -> Optional[User]: ...
    async def get_by_email(self, email: str) -> Optional[User]: ...
    async def get_by_nickname(self, nickname: str) -> Optional[User]: ...
    async def project_registered(self, event: UserRegistered) -> User: ...

    async def find_registered_since(self, moment: datetime) -> list[User]:
        """Accounts registered at or after ``moment``, newest first.

        A read-model query rather than an aggregate load: the caller is Now's
        *New on Raketa* shelf, which wants who arrived and never wants to write
        anything back. The tie-break is the nickname and not the id, because
        ``created_at`` is a server default that every account written in one
        transaction shares, and a tie broken on a random uuid is an order that
        changes between runs.
        """
        ...

    async def find_by_ids(self, user_ids: Sequence[UUID]) -> list[User]:
        """The accounts these ids name, in no particular order.

        Silently short when an id names nobody. The caller holds a set that may
        be up to fifteen minutes old, so an account that has gone since is an
        ordinary outcome and not a reason to fail a home screen.
        """
        ...
