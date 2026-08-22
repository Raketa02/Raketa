"""Open a new policy version. The row in force is closed, never updated."""

from __future__ import annotations

from app.application.ports import UnitOfWork
from app.kernel import Clock, instant

from app.modules.clubs.application.commands import ChangeClubPolicyCommand
from app.modules.clubs.domain.club import Club
from app.modules.clubs.domain.errors import ClubNotFound
from app.modules.clubs.domain.ports import ClubRepository


class ChangeClubPolicy:
    """Author a policy version.

    ADR-0077's consequence to keep in view: this is two statements, and getting
    it wrong is silent. They are in one transaction here, and the series type
    refuses to produce a state where they have come apart in memory.
    """

    def __init__(
        self, clubs: ClubRepository, uow: UnitOfWork, clock: Clock
    ) -> None:
        self._clubs = clubs
        self._uow = uow
        self._clock = clock

    async def execute(self, command: ChangeClubPolicyCommand) -> Club:
        club = await self._clubs.get(command.club_id)
        if club is None:
            raise ClubNotFound()

        club.change_policy(command.policy, at=instant(self._clock.now()))
        stored = await self._clubs.save(club)
        await self._uow.commit()
        return stored
