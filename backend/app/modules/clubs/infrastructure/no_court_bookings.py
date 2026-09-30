"""``CourtBookings`` while nothing can be booked (#541 builds the Booking).

**Nought, and that is the truth rather than a placeholder**: no booking exists
anywhere, so no court hour is held by one — a court may be deleted, any hour
closed, and a club's whole pattern is what it can sell. The day bookings land,
an adapter over them is built in the composition root instead, and every act
that asks already refuses what it should (``court_has_bookings``,
``court_booked_then``).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import final
from uuid import UUID

from app.kernel import Instant
from app.modules.clubs.domain.ports import TakenCourtHour


@final
class NoCourtBookings:
    async def taken(
        self, club_id: UUID, *, start: Instant, end: Instant | None = None
    ) -> Sequence[TakenCourtHour]:
        return ()
