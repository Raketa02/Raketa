"""Create a club, with the first row of each of its two club-wide series."""

from __future__ import annotations

from app.application.ports import UnitOfWork
from app.kernel import Clock, instant

from app.modules.clubs.application.commands import RegisterClubCommand
from app.modules.clubs.domain.club import Club
from app.modules.clubs.domain.errors import ClubNameAlreadyUsed
from app.modules.clubs.domain.ports import ClubRepository
from app.modules.clubs.domain.value_objects import zone_named
from app.shared.ids import new_uuid


class RegisterClub:
    """Register a venue.

    Reads by name before inserting, the same way ``RegisterUser`` does, so a
    second registration is a domain conflict rather than a constraint violation
    surfacing three frames away. The unique index behind it is still what makes
    the rule true under a race.
    """

    def __init__(
        self, clubs: ClubRepository, uow: UnitOfWork, clock: Clock
    ) -> None:
        self._clubs = clubs
        self._uow = uow
        self._clock = clock

    async def execute(self, command: RegisterClubCommand) -> Club:
        if await self._clubs.get_by_name(command.name) is not None:
            raise ClubNameAlreadyUsed()

        club = Club.found(
            club_id=new_uuid(),
            name=command.name,
            address=command.address,
            point=command.point,
            timezone=zone_named(command.timezone),
            pricing=command.pricing,
            policy=command.policy,
            payout=command.payout,
            at=instant(self._clock.now()),
        )
        stored = await self._clubs.add(club)
        await self._uow.commit()
        return stored
