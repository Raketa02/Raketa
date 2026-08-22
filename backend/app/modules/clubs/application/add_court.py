"""Put a court in the catalogue: its first, open catalogue row."""

from __future__ import annotations

from app.application.ports import UnitOfWork
from app.kernel import Clock, instant

from app.modules.clubs.application.commands import AddCourtCommand
from app.modules.clubs.domain.catalogue import Court
from app.modules.clubs.domain.errors import ClubNotFound
from app.modules.clubs.domain.ports import ClubRepository
from app.shared.ids import new_uuid


class AddCourt:
    def __init__(
        self, clubs: ClubRepository, uow: UnitOfWork, clock: Clock
    ) -> None:
        self._clubs = clubs
        self._uow = uow
        self._clock = clock

    async def execute(self, command: AddCourtCommand) -> Court:
        club = await self._clubs.get(command.club_id)
        if club is None:
            raise ClubNotFound()

        court = club.add_court(
            court_id=new_uuid(),
            category_id=command.category_id,
            label=command.label,
            at=instant(self._clock.now()),
        )
        await self._clubs.save(club)
        await self._uow.commit()
        return court
