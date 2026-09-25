"""An administratorship as the club's Administrators table reads it.

**Every status is derived** (``docs/adr/0184`` §1): *active* with when the
profile was last used, *invited* with when it expires, *expired* with when it
did. And whether the club may reset this person's password — only for an
account holding nothing but administrator profiles (§6) — so the website draws
*Reset password* exactly where the backend would allow it.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Optional, final
from uuid import UUID

from app.kernel import Instant
from app.modules.administrators.domain.administrator import (
    Administrator,
    AdministratorStanding,
    AdministratorState,
)
from app.modules.administrators.domain.ports import (
    AccountHolders,
    AdministratorListing,
)


@final
@dataclass(frozen=True, slots=True)
class AdministratorGroup:
    """An official group an administrator runs. None exist yet: official
    groups arrive with #509, and the list names them with #510."""

    id: UUID
    name: str


@final
@dataclass(frozen=True, slots=True)
class AdministratorRow:
    id: UUID
    name: str
    email: str
    standing: AdministratorStanding
    #: On an *active* row only.
    last_used_at: Optional[Instant]
    #: On an *invited* or *expired* row only: when it expires, or expired.
    expires_at: Optional[Instant]
    can_reset_password: bool
    groups: Sequence[AdministratorGroup] = ()


def listing_of(administrator: Administrator) -> AdministratorListing:
    """The row an act just wrote, read off the aggregate that wrote it. Every
    act that answers a row leaves the person *invited*, where *last used* is
    not shown."""

    return AdministratorListing(
        id=administrator.id,
        club_id=administrator.club_id,
        email=administrator.email.value,
        name=administrator.name.value,
        state=administrator.state,
        account_id=administrator.account_id,
        expires_at=administrator.expires_at,
        last_used_at=None,
    )


async def row_of(
    listing: AdministratorListing, *, now: Instant, accounts: AccountHolders
) -> AdministratorRow:
    """One row, now. *Can reset* costs one read of the account per row that
    has one — a club's staff is a handful of people."""

    active = listing.state is AdministratorState.ACTIVE
    return AdministratorRow(
        id=listing.id,
        name=listing.name,
        email=listing.email,
        standing=listing.standing(now=now),
        last_used_at=listing.last_used_at if active else None,
        expires_at=None if active else listing.expires_at,
        can_reset_password=(
            listing.account_id is not None
            and not await accounts.acts_as_player(listing.account_id)
        ),
    )
