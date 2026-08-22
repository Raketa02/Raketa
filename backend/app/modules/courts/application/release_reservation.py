"""Give a court back, and keep the row.

The one act the hold ladder needs from this context when it withdraws a
speculative hold (ADR-0031, `Raketa02/Raketa#71`), and the one a cancelled
booking needs. It is a **write on the reservation, never a delete**, because
ADR-0035's *"a court's booking history is a query over reservations"* stops being
true the moment a row can vanish — and because the exclusion constraint is
partial over the live rows, a released row costs the next claimant nothing.
"""

from __future__ import annotations

from app.application.ports import UnitOfWork
from app.kernel import Clock, instant

from app.modules.courts.application.commands import ReleaseReservationCommand
from app.modules.courts.domain.errors import ReservationNotFound
from app.modules.courts.domain.ports import ReservationRepository
from app.modules.courts.domain.reservation import Reservation


class ReleaseReservation:
    """Give the court back, keeping the row and its history."""

    def __init__(
        self,
        reservations: ReservationRepository,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._reservations = reservations
        self._uow = uow
        self._clock = clock

    async def execute(self, command: ReleaseReservationCommand) -> Reservation:
        reservation = await self._reservations.get(command.reservation_id)
        if reservation is None:
            raise ReservationNotFound()

        reservation.release(at=instant(self._clock.now()))
        saved = await self._reservations.save(reservation)
        await self._uow.commit()
        return saved
