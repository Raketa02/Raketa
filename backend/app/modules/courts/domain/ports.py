"""The Courts-and-Bookings ports.

Two **record** repositories, the kind `app/modules/clubs/domain/ports.py`
introduced: rows in, rows out, and the optimistic-concurrency guard is a version
column rather than a stream version (ADR-0034 applied one context over).

``save`` does not commit. The transaction boundary stays a use-case dependency,
and here it is load-bearing in a way it is nowhere else: ADR-0035 fixes that *"a
seat payment that earns a court, and the court it earns, are one event or they
are a bug"*, so the write that claims a court has to be joinable to a write in
another context. A repository that committed would make that impossible from the
outside.

**``add`` raises ``CourtAlreadyClaimed`` and it is not an exception in the
ordinary sense.** It is the exclusion constraint answering, and the answer means
*look again* — the caller re-scans and either finds another court or reports
``InventoryLost``. The adapter must therefore leave the surrounding transaction
usable, which is why the insert happens inside a savepoint.
"""

from __future__ import annotations

from typing import Protocol, Sequence, runtime_checkable
from uuid import UUID

from app.modules.courts.domain.booking import Booking
from app.modules.courts.domain.reservation import Reservation
from app.modules.courts.domain.time_range import TimeRange


@runtime_checkable
class ReservationRepository(Protocol):
    async def get(self, reservation_id: UUID) -> Reservation | None:
        """One reservation, whole, or nothing."""
        ...

    async def overlapping(
        self, *, court_ids: Sequence[UUID], window: TimeRange
    ) -> list[Reservation]:
        """Every **live** reservation on any of those courts touching ``window``.

        Deliberately not *"the free courts"*: the decision is
        `app/modules/courts/domain/availability.py`'s and is pure, so the same
        facts always yield the same court. This is the fetch, and it is narrowed
        by court and by window because a club's whole history is not an input to
        *is court 3 free on Tuesday*.
        """
        ...

    async def for_court(self, court_id: UUID) -> list[Reservation]:
        """A court's booking history — released rows included, oldest first.

        ADR-0035: *"a court's booking history is a query over reservations"*.
        This is that query, and it is why a release keeps the row.
        """
        ...

    async def add(self, reservation: Reservation) -> Reservation:
        """Claim the court, or refuse with ``CourtAlreadyClaimed``.

        The refusal comes from the database's exclusion constraint, never from
        read ordering, and it leaves the surrounding transaction usable.
        """
        ...

    async def save(self, reservation: Reservation) -> Reservation:
        """Persist a release or a reassignment, refusing on a stale version.

        Raises ``ConcurrentReservationModification`` when the stored version has
        moved, and ``CourtAlreadyClaimed`` when a reassignment would overlap.
        """
        ...


@runtime_checkable
class BookingRepository(Protocol):
    async def get(self, booking_id: UUID) -> Booking | None: ...

    async def for_reservation(self, reservation_id: UUID) -> Booking | None:
        """The booking holding this claim, if one does.

        A match hold and a club block have none, which is the shape of *"a
        Booking holds a Reservation and is not one"* seen from the other side.
        """
        ...

    async def for_player(self, player_id: UUID) -> list[Booking]:
        """Everything this player has bought, newest first."""
        ...

    async def add(self, booking: Booking) -> Booking: ...

    async def save(self, booking: Booking) -> Booking: ...
