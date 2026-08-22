"""Take a court out of the catalogue by closing its open row."""

from __future__ import annotations

from app.application.ports import UnitOfWork
from app.kernel import Clock, instant

from app.modules.clubs.application.commands import RetireCourtCommand
from app.modules.clubs.domain.catalogue import Court
from app.modules.clubs.domain.errors import ClubNotFound
from app.modules.clubs.domain.ports import ClubRepository


class RetireCourt:
    """A retirement shrinks availability, and that is why it is remembered.

    ``inventoryLost`` is terminal — it cancels the match and refunds everybody —
    so *nothing was free* has to be answerable afterwards: whether because
    everything was booked, or because the club retired the court (ADR-0077).
    """

    def __init__(
        self, clubs: ClubRepository, uow: UnitOfWork, clock: Clock
    ) -> None:
        self._clubs = clubs
        self._uow = uow
        self._clock = clock

    async def execute(self, command: RetireCourtCommand) -> Court:
        club = await self._clubs.get(command.club_id)
        if club is None:
            raise ClubNotFound()

        court = club.retire_court(command.court_id, at=instant(self._clock.now()))
        await self._clubs.save(club)
        await self._uow.commit()
        return court
