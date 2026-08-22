"""Move a court into another category, or relabel it — a new catalogue row."""

from __future__ import annotations

from app.application.ports import UnitOfWork
from app.kernel import Clock, instant

from app.modules.clubs.application.commands import MoveCourtCommand
from app.modules.clubs.domain.catalogue import Court
from app.modules.clubs.domain.errors import ClubNotFound
from app.modules.clubs.domain.ports import ClubRepository


class MoveCourt:
    """Not to be confused with reassignment.

    Reassigning a player's booking from one court to another *of the same
    category* is ordinary and happens on the reservation; it never touches the
    catalogue and never changes the published category or the quoted price
    (ADR-0035, ADR-0079). This is the club rearranging its own groups, which is a
    fact about the venue and is therefore remembered.
    """

    def __init__(
        self, clubs: ClubRepository, uow: UnitOfWork, clock: Clock
    ) -> None:
        self._clubs = clubs
        self._uow = uow
        self._clock = clock

    async def execute(self, command: MoveCourtCommand) -> Court:
        club = await self._clubs.get(command.club_id)
        if club is None:
            raise ClubNotFound()

        court = club.move_court(
            command.court_id,
            category_id=command.category_id,
            label=command.label,
            at=instant(self._clock.now()),
        )
        await self._clubs.save(club)
        await self._uow.commit()
        return court
