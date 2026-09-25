"""**The administrator guard** (``docs/adr/0184`` §7), and the one read it
proves itself on.

Every administrator operation names its club and is checked, on every request,
for **an active administratorship of this account at that club** — the
authority is not in the token (``docs/adr/0185`` §6), so a removal takes effect
on the next request with no push and no revocation list. The refusal is one
distinct code, ``not_an_administrator``, which the app turns into a message and
a move to the player profile.

The guard is also where *last used* moves — at most once an hour, because a
write on every administrator request would add one to every read
(``docs/adr/0184`` §1).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.application.ports import UnitOfWork
from app.kernel import Clock
from app.modules.administrators.domain.administrator import LAST_USED_GRANULARITY
from app.modules.administrators.domain.errors import NotAnAdministrator
from app.modules.administrators.domain.ports import (
    AdministratorDirectory,
    AdministratorListing,
    ClubNames,
    club_name_of,
)


class ActiveAdministratorship:
    def __init__(
        self,
        *,
        directory: AdministratorDirectory,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._directory = directory
        self._uow = uow
        self._clock = clock

    async def execute(self, *, account_id: UUID, club_id: UUID) -> AdministratorListing:
        listing = await self._directory.active_at(club_id, account_id)
        if listing is None:
            raise NotAnAdministrator(club_id)
        now = self._clock.now()
        if (
            listing.last_used_at is None
            or now - listing.last_used_at >= LAST_USED_GRANULARITY
        ):
            # Its own commit, before the operation it guards: a use is a use
            # whether or not the operation behind it is then refused.
            await self._directory.record_use(listing.id, at=now)
            await self._uow.commit()
        return listing


@final
@dataclass(frozen=True, slots=True)
class AdministratorProfile:
    """*My administrator profile at club X*: the guarded read the app opens
    the administrator area on."""

    club_id: UUID
    club_name: str


class ReadAdministratorProfile:
    def __init__(self, *, clubs: ClubNames) -> None:
        self._clubs = clubs

    async def execute(
        self, administratorship: AdministratorListing
    ) -> AdministratorProfile:
        club_id = administratorship.club_id
        return AdministratorProfile(
            club_id=club_id, club_name=await club_name_of(self._clubs, club_id)
        )
