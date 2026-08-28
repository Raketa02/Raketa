from __future__ import annotations

from typing import Collection, Mapping, Optional, Protocol, runtime_checkable
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

    async def find_nicknames_of(
        self, user_ids: Collection[UUID]
    ) -> Mapping[UUID, str]:
        """What each of these accounts is called, as one set read.

        Asked by the matcher, which puts a **nickname** on a player card and
        holds no name of its own (``docs/adr/0107``) — and answered here rather
        than by a reader of this context's table, on the rule its neighbour above
        states: a consumer-driven contract is satisfied by the **provider**, and
        ``users`` owns what an account is called and where that is stored.

        A mapping and not a per-id question, because the caller has a whole
        shortlist and asks once. **An id this context has never seen is simply
        absent from the answer** — the caller drops the row rather than drawing a
        card with a blank name, and inventing a placeholder here would be this
        context answering for an account it does not have.
        """
        ...
