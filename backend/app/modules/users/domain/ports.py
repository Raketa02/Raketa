from __future__ import annotations

from dataclasses import dataclass
from typing import Collection, Mapping, Optional, Protocol, final, runtime_checkable
from uuid import UUID

from app.modules.users.domain.events import (
    AccountOpenedByInvitation,
    PasswordChanged,
    PasswordCleared,
    UserNamed,
    UserRegistered,
)
from app.modules.users.domain.user import User


@final
@dataclass(frozen=True, slots=True)
class Naming:
    """How a named player is seen: the **name** every screen says, and the
    **nickname** drawn as ``@…`` on their record and their own You tab
    (``docs/adr/0171`` §1).

    Both or neither — the naming is one act carrying both — so a read that
    answers with one of these answers with the pair, and an account that has
    neither is simply absent from the answer.
    """

    name: str
    nickname: str


@runtime_checkable
class UserRepository(Protocol):
    async def get_by_id(self, user_id: UUID) -> Optional[User]: ...
    async def get_by_email(self, email: str) -> Optional[User]: ...

    async def get_by_nickname(self, nickname: str) -> Optional[User]:
        """The account holding this handle, if any.

        The one uniqueness read the naming makes (``docs/adr/0171`` §2): the
        act refuses with ``NicknameAlreadyTaken`` when the holder is somebody
        else, and admits a player keeping their own.
        """
        ...

    async def project_registered(self, event: UserRegistered) -> User: ...

    async def project_opened_by_invitation(
        self, event: AccountOpenedByInvitation
    ) -> User:
        """Write the row for an account an Invitation opened, **with the name
        the club typed and no nickname**, in the act's own transaction
        (``docs/adr/0185`` §4)."""
        ...

    async def project_named(self, event: UserNamed) -> User:
        """Write the naming onto the projection row, in the act's own transaction.

        The read model is written beside the event and never behind it
        (``docs/adr/0002``'s CQRS-lite), which is what lets the uniqueness read
        above see a nickname the instant it is taken.
        """
        ...

    async def project_password_changed(self, event: PasswordChanged) -> None:
        """Write the new hash and the credentials-changed instant onto the
        projection row, in the act's own transaction (``docs/adr/0185`` §7).

        On the row because sign-in reads the hash from it and every request
        reads the instant from it — a change on the stream alone would leave
        the old password working and the old sessions open.
        """
        ...

    async def project_password_cleared(self, event: PasswordCleared) -> None:
        """Clear the hash and move the credentials-changed instant on the row,
        in the act's own transaction (``docs/adr/0184`` §6): sign-in reads the
        hash from the row, so a password cleared on the stream alone would
        still sign in."""
        ...

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

    async def find_namings_of(
        self, user_ids: Collection[UUID]
    ) -> Mapping[UUID, Naming]:
        """What each of these accounts is called, as one set read.

        Asked by every context that puts a **name** on a card, a seat or a
        member and holds no name of its own (``docs/adr/0107``, ``docs/adr/0171``
        §4) — and answered here rather than by a reader of this context's
        table, on the rule its neighbour above states: a consumer-driven
        contract is satisfied by the **provider**, and ``users`` owns what an
        account is called and where that is stored.

        A mapping and not a per-id question, because the caller has a whole
        shortlist and asks once. **An id this context has never seen is absent
        from the answer, and so is an account not yet named** — the caller
        drops a card it cannot name and keeps a seat with ``None`` on it, and
        inventing a placeholder here would be this context answering for an
        account it does not have. The gate holds an unnamed account at the
        naming step, so the second absence is one no surface should reach; a
        ``?`` drawn for a person who exists is where it would first show.
        """
        ...
