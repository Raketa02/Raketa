"""Swap which court a live reservation names. Ordinary — and re-checked.

ADR-0035 names this as the sharpest new cost of the decision: *"Reassignment is
now something that can be got wrong. Swapping a live reservation's court must
re-check exclusion, and a swap that silently fails leaves the match pointing at a
court somebody else holds — the original defect, moved downstream."*

So the re-check is not written here. It is the same exclusion constraint, on the
same UPDATE, and `CourtAlreadyClaimed` is raised by the adapter when the database
refuses. A hand-written overlap query in this file would be the second
implementation the constraint exists to make unnecessary, and it would be the one
that is wrong under a race.

**Within the category, and nothing else moves.** The category was bought; the
price was copied onto the booking at booking time; the two intervals describe a
game, and moving a court does not move a game.
"""

from __future__ import annotations

from app.application.ports import UnitOfWork

from app.modules.clubs.domain.errors import ClubNotFound
from app.modules.clubs.domain.ports import ClubRepository
from app.modules.courts.application.commands import ReassignCourtCommand
from app.modules.courts.domain.errors import (
    CourtNotInCategory,
    ReservationNotFound,
)
from app.modules.courts.domain.ports import ReservationRepository
from app.modules.courts.domain.reservation import Reservation


class ReassignCourt:
    def __init__(
        self,
        clubs: ClubRepository,
        reservations: ReservationRepository,
        uow: UnitOfWork,
    ) -> None:
        self._clubs = clubs
        self._reservations = reservations
        self._uow = uow

    async def execute(self, command: ReassignCourtCommand) -> Reservation:
        reservation = await self._reservations.get(command.reservation_id)
        if reservation is None:
            raise ReservationNotFound()

        club = await self._clubs.get(reservation.club_id)
        if club is None:  # pragma: no cover - a reservation names a real club
            raise ClubNotFound()

        # The **live** courts of the reservation's own category. A retired court
        # is not a target: the club has said it may not be assigned, and moving
        # a live claim onto one is how a match ends up on a court that no longer
        # exists (ADR-0079).
        eligible = {court.id for court in club.courts_in(reservation.category_id)}
        if command.court_id not in eligible:
            raise CourtNotInCategory()

        reservation.reassign_to(command.court_id)
        saved = await self._reservations.save(reservation)
        await self._uow.commit()
        return saved
