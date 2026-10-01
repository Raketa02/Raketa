"""``BookingHistoryQuery`` over the projections and the streams (#544).

**Who ever held a seat is the projection's** — ``booking_seats`` keeps a leaver's
row, marked — and **what became of it is the stream's**, folded by the domain's
own rule (``keeping.py``) against the caller's clock, so a game short at its
cut-off is a mark from the cut-off on whether or not the job has recorded it.

**Cost.** One stream read per booking a player ever held a seat on, each folded
once per question however many of the asked players sat on it: a handful per
player today, and the matcher's ~500 candidates make it the one read here worth
batching — the event store has no many-streams read yet, and it belongs with the
first query that measures it.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Collection, Mapping
from typing import final
from uuid import UUID

from app.kernel import Instant
from app.modules.bookings.domain.booking import Booking
from app.modules.bookings.domain.keeping import KeepingRecord, keeping_of
from app.modules.bookings.domain.ports import BookingDirectory, BookingRepository


@final
class EventSourcedBookingHistory:
    def __init__(
        self, *, directory: BookingDirectory, bookings: BookingRepository
    ) -> None:
        self._directory = directory
        self._bookings = bookings

    async def keeping_for(
        self, player_ids: Collection[UUID], *, now: Instant
    ) -> Mapping[UUID, KeepingRecord]:
        kept: dict[UUID, int] = defaultdict(int)
        broken: dict[UUID, int] = defaultdict(int)
        latest: dict[UUID, Instant] = {}
        folded: dict[UUID, Booking | None] = {}
        for player_id, booking_id in await self._directory.ever_seated(player_ids):
            if booking_id not in folded:
                folded[booking_id] = await self._bookings.load(booking_id)
            booking = folded[booking_id]
            keeping = (
                None if booking is None else keeping_of(booking, player_id, now=now)
            )
            if keeping is None:
                continue
            if keeping.kept:
                kept[player_id] += 1
            else:
                broken[player_id] += 1
            latest[player_id] = max(keeping.at, latest.get(player_id, keeping.at))
        return {
            player_id: KeepingRecord(
                kept=kept[player_id], broken=broken[player_id], last_at=at
            )
            for player_id, at in latest.items()
        }
