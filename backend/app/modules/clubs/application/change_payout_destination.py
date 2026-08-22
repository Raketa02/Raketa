"""Open a new payout-destination version.

Its own series rather than a field of the policy row, and the reason is fraud:
ops tunes a hold cap and finance changes a bank account, so folding them means
every routine tweak re-asserts the bank details (ADR-0077).
"""

from __future__ import annotations

from app.application.ports import UnitOfWork
from app.kernel import Clock, instant

from app.modules.clubs.application.commands import ChangePayoutDestinationCommand
from app.modules.clubs.domain.club import Club
from app.modules.clubs.domain.errors import ClubNotFound
from app.modules.clubs.domain.ports import ClubRepository


class ChangePayoutDestination:
    def __init__(
        self, clubs: ClubRepository, uow: UnitOfWork, clock: Clock
    ) -> None:
        self._clubs = clubs
        self._uow = uow
        self._clock = clock

    async def execute(self, command: ChangePayoutDestinationCommand) -> Club:
        club = await self._clubs.get(command.club_id)
        if club is None:
            raise ClubNotFound()

        club.change_payout_destination(
            command.destination, at=instant(self._clock.now())
        )
        stored = await self._clubs.save(club)
        await self._uow.commit()
        return stored
