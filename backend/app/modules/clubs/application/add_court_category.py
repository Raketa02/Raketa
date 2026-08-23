"""Declare a group of interchangeable courts, and what one block of it costs."""

from __future__ import annotations

from app.application.ports import UnitOfWork
from app.kernel import Clock

from app.modules.clubs.application.commands import AddCourtCategoryCommand
from app.modules.clubs.domain.catalogue import CourtCategory
from app.modules.clubs.domain.errors import ClubNotFound
from app.modules.clubs.domain.ports import ClubRepository
from app.shared.ids import new_uuid


class AddCourtCategory:
    """The club groups its own courts; the platform constrains two facts.

    Neither constraint is arbitrary. A sport's player count is read from exactly
    one place everywhere, and a category spanning two sports would make a seat
    share undefined (ADR-0079); a category spanning two roofs would make the
    spine of every card at that club lie about the fact a player is choosing on
    in November (ADR-0090). Both are expressed in the type — a category has one
    ``Sport`` and one ``Cover``, and no way to hold two of either.
    """

    def __init__(
        self, clubs: ClubRepository, uow: UnitOfWork, clock: Clock
    ) -> None:
        self._clubs = clubs
        self._uow = uow
        self._clock = clock

    async def execute(self, command: AddCourtCategoryCommand) -> CourtCategory:
        club = await self._clubs.get(command.club_id)
        if club is None:
            raise ClubNotFound()

        category = club.add_category(
            category_id=new_uuid(),
            name=command.name,
            sport=command.sport,
            cover=command.cover,
            rate=command.rate,
        )
        await self._clubs.save(club)
        await self._uow.commit()
        return category
