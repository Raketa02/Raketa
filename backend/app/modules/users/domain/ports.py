from __future__ import annotations

from typing import Collection, Optional, Protocol, runtime_checkable
from uuid import UUID

from app.modules.users.domain.events import UserRegistered
from app.modules.users.domain.user import User


@runtime_checkable
class UserRepository(Protocol):
    async def get_by_id(self, user_id: UUID) -> Optional[User]: ...
    async def get_by_email(self, email: str) -> Optional[User]: ...
    async def get_by_nickname(self, nickname: str) -> Optional[User]: ...
    async def project_registered(self, event: UserRegistered) -> User: ...

    async def find_disabled_among(
        self, user_ids: Collection[UUID]
    ) -> frozenset[UUID]:
        """Which of these accounts are disabled, as one set read.

        Asked by the matcher's account-state gate (``docs/adr/0124``), and
        answered here rather than by a reader of this context's table: a
        consumer-driven contract is satisfied by the **provider**, and ``users``
        owns what *disabled* means and where it is stored.

        A set and not a per-id question, because the caller has a whole
        shortlist and asks once per search. Ids this context has never seen are
        simply absent from the answer — an unknown id is not a disabled account,
        and reporting it as one would make a typo look like a safety verdict.
        """
        ...
