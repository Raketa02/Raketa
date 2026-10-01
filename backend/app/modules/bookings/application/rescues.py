"""A rescue taking an open seat, and a no to one (#545; the mechanics §10.1,
§12.3; ``docs/adr/0189`` §5).

**Two acts on one booking, each in its caller's transaction**, which is the
proposal's — the joiner's — and **nothing here commits**:

- **rescued** — the seat that opened first is taken, on its side, on the
  booking and on its Game, whose room the newcomer joins with it; who the seat
  was, and when they left, is answered, for the caller to refund the leaver
  when their seat was a paid one after the cut-off;
- **a no** — a member the seat was dealt to as a card said no to it.

Whether the joiner may — in the pool, a fit, free, paid — is the caller's
question, asked before this.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.kernel import Instant, invariant
from app.modules.bookings.domain.booking import Booking, Departure
from app.modules.bookings.domain.ports import BookingRepository, GameChanges


@final
class RescueTheSeat:
    def __init__(self, *, bookings: BookingRepository, games: GameChanges) -> None:
        self._bookings = bookings
        self._games = games

    async def execute(
        self, booking_id: UUID, player_id: UUID, *, at: Instant
    ) -> Departure:
        """The leaver whose seat this player took."""

        booking = await _loaded(self._bookings, booking_id)
        taken = booking.rescue(player_id, at=at)
        await self._bookings.save(booking)
        await self._games.seat(booking_id, player_id, side=taken.side, at=at)
        return taken


@final
class SayNoToTheSeat:
    def __init__(self, *, bookings: BookingRepository) -> None:
        self._bookings = bookings

    async def execute(self, booking_id: UUID, player_id: UUID, *, at: Instant) -> bool:
        """Whether anything was recorded — nothing for a second no."""

        booking = await _loaded(self._bookings, booking_id)
        if not booking.say_no(player_id, at=at):
            return False
        await self._bookings.save(booking)
        return True


async def _loaded(bookings: BookingRepository, booking_id: UUID) -> Booking:
    return invariant(await bookings.load(booking_id), f"no booking {booking_id}")
