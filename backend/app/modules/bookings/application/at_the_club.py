"""What the club does to its bookings (#547; the mechanics §16.7, §16.9,
§16.16; the screens B4, B6).

**Two acts and a read, each in its caller's transaction**, which is the
proposal's — every act on a game locks its proposal's row first — and
**nothing here commits**:

- **the free courts** — every other court of the game's sport the club still
  has for Raketa at its hour, in the club's order, **of a kind the players would
  accept**: the same kind, or an indoor court for an outdoor game — never
  outdoors from indoors (#671; the mechanics §16.4, Q122) — each with its kind;
- **moved** — the game is on one of them, and the players read its number and
  its kind; a move to any other court is refused;
- **cancelled** — the game is off with the club's reason, its Game and room end
  with it, and everybody it owes money to is answered, for the caller to refund
  in full.

The desk's check-in, and its reading of a code, are removed (#651).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.kernel import Instant, invariant
from app.modules.bookings.domain.booking import BookedCourt, Booking, CancelReason
from app.modules.bookings.domain.ports import (
    BookingRepository,
    ClubCourtsAtTheHour,
    GameChanges,
)


@final
class MoveTheBooking:
    def __init__(
        self, *, bookings: BookingRepository, courts: ClubCourtsAtTheHour
    ) -> None:
        self._bookings = bookings
        self._courts = courts

    async def free_courts(self, booking_id: UUID) -> tuple[BookedCourt, ...]:
        """The courts the game may be moved to: the free courts of its sport at
        its hour that keep its kind — the same kind, or indoor for an outdoor
        game (#671, Q122). The game's own is not among them: its booking holds
        it."""

        booking = await _loaded(self._bookings, booking_id)
        return tuple(
            court
            for court in await self._courts.free_courts(
                booking.club_id, sport=booking.sport, start=booking.start
            )
            if court.court_id != booking.court.court_id
            and booking.court.may_move_to(court)
        )

    async def execute(
        self, booking_id: UUID, court_id: UUID, *, at: Instant
    ) -> BookedCourt | None:
        """Move the game onto ``court_id`` — ``None`` when that is not one of
        the free courts, which records nothing. ``CourtTaken`` when another
        game claimed it a moment ago. Whether it may still be moved is the
        caller's question, asked before this."""

        court = next(
            (
                one
                for one in await self.free_courts(booking_id)
                if one.court_id == court_id
            ),
            None,
        )
        if court is None:
            return None
        booking = await _loaded(self._bookings, booking_id)
        booking.move_to(court, at=at)
        await self._bookings.save(booking)
        return court


@final
@dataclass(frozen=True, slots=True)
class Cancelled:
    """What the club's cancel owes: everybody still in — refunded in full and
    dealt a new card first — and everybody it gives money back to, which adds
    a leaver whose seat it left open and paid."""

    still_in: tuple[UUID, ...]
    refunded: tuple[UUID, ...]


@final
class CancelTheBooking:
    def __init__(self, *, bookings: BookingRepository, games: GameChanges) -> None:
        self._bookings = bookings
        self._games = games

    async def execute(
        self, booking_id: UUID, reason: CancelReason, *, at: Instant
    ) -> Cancelled:
        """Whether it may still be cancelled is the caller's question, asked
        before this."""

        booking = await _loaded(self._bookings, booking_id)
        still_in = booking.players
        # A seat left open is still paid for — after the cut-off, nobody gave
        # it back — and the club's cancel gives it back (a leaver refunded
        # already is refunded nothing twice).
        open_leavers = tuple(left.player_id for left in booking.open_departures)
        booking.cancel(reason, at=at)
        await self._bookings.save(booking)
        await self._games.call_off_whole(booking_id, at=at)
        return Cancelled(still_in=still_in, refunded=(*still_in, *open_leavers))


async def _loaded(bookings: BookingRepository, booking_id: UUID) -> Booking:
    return invariant(await bookings.load(booking_id), f"no booking {booking_id}")
