"""Who the console may act as: seed accounts, and nobody else
(``docs/adr/0194`` §2).

**The acting account** is the one a console press acts as — named in the path,
never signed in. It must be an account the seed created, addressed on the
reserved ``.example`` TLD; any other id is **refused**, and refused before the
use case is built, so nothing is recorded. It must also be one the player's own
route would serve — still active — since a press does what that person's button
does, refusals included. The old console could treat this as
a filter, because its only door was the ordinary login, which takes any
credential anyway. Now the console's route is the door, so the check has to be
a refusal.

**A read about somebody** — their *Sent* pane — refuses the same ids but
presses nothing, so it takes the account (``SeedAccountDep``) without the
player route's own step.

**One rule for the roster and the refusal**: ``is_seed_account`` is what the
console asks of the account it is about to act as, and ``seed_accounts_only`` is
the same rule in SQL, which the roster and the board run. The TLD is the seed
catalog's own, imported — the console is built from the seed's building blocks
(ADR-0194 §4), so there is one spelling of it.
"""

from __future__ import annotations

import app.api.dev.refusal  # noqa: F401 — refuses first; see refusal.py

from typing import Annotated
from uuid import UUID

from fastapi import Depends, Path
from sqlalchemy.sql.elements import ColumnElement

from app.api.dependencies import UserRepositoryDep
from app.modules.users.domain.ports import UserRepository
from app.modules.users.domain.user import User
from app.modules.users.presentation.dependencies import GetCurrentUserUseCaseDep
from app.modules.users.infrastructure.sqlalchemy_user_model import UserORM
from app.seeds.catalog import RESERVED_TLD
from app.shared.domain.errors import ForbiddenError


class NotASeedAccount(ForbiddenError):
    """The console was asked to act as an account the seed did not create — or
    as an id that is nobody's, which is not one either. One code for both."""

    code = "not_a_seed_account"

    def __init__(self) -> None:
        super().__init__(
            "The console acts only as seed accounts — addressed on the reserved "
            f"'{RESERVED_TLD}' TLD — and this is not one."
        )


def is_seed_account(email: str) -> bool:
    """Is this address a fabricated one — on the TLD RFC 2606 §2 reserves, which
    no registry will ever sell, so it cannot be somebody's real mailbox?

    Total: a string with no ``@`` has no domain, so it is **not** a seed account
    rather than an error. The ``@`` is checked rather than assumed: without it
    ``rpartition`` hands back the whole string, and ``nonsense.example`` would
    read as an address on the reserved TLD.
    """

    local, at, domain = email.rpartition("@")
    return bool(local) and bool(at) and domain.casefold().endswith(RESERVED_TLD)


def seed_accounts_only() -> ColumnElement[bool]:
    """``is_seed_account`` written in SQL, over ``UserORM.email``.

    Two spellings of one predicate, because a list must not load a real
    database's users into this process to filter them — and they cannot drift
    far, since the domain is everything after the last ``@`` and an address ends
    where its domain does, so a case-insensitive suffix match is the same claim.
    The ``%@%`` is the ``@`` the Python side checks for, and it is here for the
    same reason: without it the pattern matches a string that is not an address
    at all. ``tests/api/test_dev_console.py`` registers addresses on both sides
    of the line and asserts the two agree.
    """

    return UserORM.email.ilike(f"_%@%{RESERVED_TLD}")


async def _seed_user(users: UserRepository, player_id: UUID) -> User | None:
    user = await users.get_by_id(player_id)
    return user if user is not None and is_seed_account(user.email.value) else None


async def holds_a_seed_account(users: UserRepository, player_id: UUID) -> bool:
    """Whether this id is an account the seed created — ``False`` for an id that
    is nobody's, which is not one either."""

    return await _seed_user(users, player_id) is not None


async def the_seed_account(users: UserRepository, player_id: UUID) -> User:
    """The account itself, once it is one the seed created — refused otherwise."""

    user = await _seed_user(users, player_id)
    if user is None:
        raise NotASeedAccount()
    return user


async def refuse_unless_a_seed_account(users: UserRepository, player_id: UUID) -> None:
    await the_seed_account(users, player_id)


async def acting_account(
    player_id: Annotated[
        UUID,
        Path(
            description=(
                "The acting account: the seed account this press acts as. Any "
                "other id is refused `not_a_seed_account`."
            )
        ),
    ],
    users: UserRepositoryDep,
    current: GetCurrentUserUseCaseDep,
) -> UUID:
    """The acting account's id, once it is one the console may act as — and
    one the player's own route would serve: ``GetCurrentUser`` is the step every
    player route takes after reading the token, and it refuses an account that
    is no longer active, in its own words (``user_not_eligible``)."""

    await refuse_unless_a_seed_account(users, player_id)
    await current.execute(player_id)
    return player_id


ActingDep = Annotated[UUID, Depends(acting_account)]


async def seed_account_in_path(
    player_id: Annotated[
        UUID,
        Path(
            description=(
                "The seed account this read is about. Any other id is refused "
                "`not_a_seed_account`."
            )
        ),
    ],
    users: UserRepositoryDep,
) -> User:
    """The account a read is about (#594). **Not the acting account**: a read
    presses nothing, so there is no player route whose refusals it must share —
    what was sent to an account since disabled is still worth reading."""

    return await the_seed_account(users, player_id)


SeedAccountDep = Annotated[User, Depends(seed_account_in_path)]
