"""Retire a category — and, with it, every court still in it."""

from __future__ import annotations

from app.application.ports import UnitOfWork
from app.kernel import Clock, instant

from app.modules.clubs.application.commands import RetireCourtCategoryCommand
from app.modules.clubs.domain.catalogue import CourtCategory
from app.modules.clubs.domain.errors import ClubNotFound
from app.modules.clubs.domain.ports import ClubRepository


class RetireCourtCategory:
    """Retired, never deleted (ADR-0079).

    A past reservation names the court it claimed and the quoted price was
    copied onto the match at booking, so nothing has to query a category as of a
    past instant. What retirement buys is that the record still parses — which
    is the second half of making ``inventoryLost`` explicable.
    """

    def __init__(
        self, clubs: ClubRepository, uow: UnitOfWork, clock: Clock
    ) -> None:
        self._clubs = clubs
        self._uow = uow
        self._clock = clock

    async def execute(self, command: RetireCourtCategoryCommand) -> CourtCategory:
        club = await self._clubs.get(command.club_id)
        if club is None:
            raise ClubNotFound()

        category = club.retire_category(
            command.category_id, at=instant(self._clock.now())
        )
        await self._clubs.save(club)
        await self._uow.commit()
        return category
