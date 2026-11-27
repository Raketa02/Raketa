"""What the club does to its bookings (#547; the mechanics §16.7, §16.9,
§16.16; the screens B4, B6).

**Two acts and a read, each in its caller's transaction**, which is the
proposal's — every act on a game locks its proposal's row first — and
**nothing here commits**:

- **the free courts** — every other court of the game's sport the club still
  has for Rakieta at its hour, in the club's order, **of a kind the players would
  accept**: the same kind, or an indoor court for an outdoor game — never
  outdoors from indoors (#671; the mechanics §16.4, Q122) — each with its kind;
- **moved** — the game is on one of them, and the players read its number and
  its kind; a move to any other court is refused;
- **cancelled** — **unless a free court absorbs it** (#672; the mechanics
  §16.9, Q122): another court of the club's at the game's hour, sold at its
  share, of its kind or indoor for an outdoor game, and indoor for *weather*.
  Then the game moves there, the cancel's reason on the move, and nothing else
  happens: nobody is refunded, let go or owed a card. Otherwise — or *anyway*
  — the game is off with the club's reason, its Game and room end with it, and
  everybody it owes money to is answered, for the caller to refund in full.
  Which court absorbs it is read afresh at every press, so a preview a moment
  old never decides it. **Either way the court it was on is closed for the
  hour** (#673): it can't be played then, so it is never sold for that hour
  again — to these players' owed card or to anybody — until the club opens it.

The desk's check-in, and its reading of a code, are removed (#651).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.kernel import Instant, invariant
from app.modules.bookings.domain.booking import (
    BookedCourt,
    Booking,
    CancelReason,
    FreeCourt,
)
from app.modules.bookings.domain.ports import (
    BookingRepository,
    ClubCourtsAtTheHour,
    CourtClosures,
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
            one.court
            for one in await _free_at_its_hour(self._courts, booking)
            if one.court.court_id != booking.court.court_id
            and booking.court.may_move_to(one.court)
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
@dataclass(frozen=True, slots=True)
class MovedByCancel:
    """The club's cancel a free court absorbed (#672): the game is on
    ``court`` now, and nothing is owed to anybody."""

    court: BookedCourt


@final
class CancelTheBooking:
    def __init__(
        self,
        *,
        bookings: BookingRepository,
        games: GameChanges,
        courts: ClubCourtsAtTheHour,
        closures: CourtClosures,
    ) -> None:
        self._bookings = bookings
        self._games = games
        self._courts = courts
        self._closures = closures

    async def absorbing_court(
        self, booking_id: UUID, reason: CancelReason
    ) -> BookedCourt | None:
        """The court a cancel for ``reason`` would move the game to now — the
        cancel dialog's preview — or ``None`` when it would call the game
        off."""

        return await self._absorbing(await _loaded(self._bookings, booking_id), reason)

    async def execute(
        self, booking_id: UUID, reason: CancelReason, *, anyway: bool, at: Instant
    ) -> MovedByCancel | Cancelled:
        """A move by cancel when a free court absorbs it, read afresh now —
        or, ``anyway`` or with none, the game called off. ``CourtTaken`` when
        another game claimed the absorbing court a moment ago. Whether it may
        still be cancelled is the caller's question, asked before this."""

        booking = await _loaded(self._bookings, booking_id)
        its_court = booking.court
        court = None if anyway else await self._absorbing(booking, reason)
        if court is not None:
            booking.move_to(court, at=at, because=reason)
            await self._bookings.save(booking)
            await self._close(booking, its_court, reason, at=at)
            return MovedByCancel(court=court)
        still_in = booking.players
        # A seat left open is still paid for — after the cut-off, nobody gave
        # it back — and the club's cancel gives it back (a leaver refunded
        # already is refunded nothing twice).
        open_leavers = tuple(left.player_id for left in booking.open_departures)
        booking.cancel(reason, at=at)
        await self._bookings.save(booking)
        await self._games.call_off_whole(booking_id, at=at)
        await self._close(booking, its_court, reason, at=at)
        return Cancelled(still_in=still_in, refunded=(*still_in, *open_leavers))

    async def _close(
        self, booking: Booking, court: BookedCourt, reason: CancelReason, *, at: Instant
    ) -> None:
        """The court the club cancelled, closed for the hour — once the
        booking's save has freed it."""

        await self._closures.close(
            booking.club_id, court.court_id, start=booking.start, because=reason, at=at
        )

    async def _absorbing(
        self, booking: Booking, reason: CancelReason
    ) -> BookedCourt | None:
        return booking.absorbing_court(
            await _free_at_its_hour(self._courts, booking), because=reason
        )


async def _free_at_its_hour(
    courts: ClubCourtsAtTheHour, booking: Booking
) -> Sequence[FreeCourt]:
    """Every court of the game's sport its club still sells at its hour, in
    the club's order — its own excluded, since its booking holds it."""

    return await courts.free_courts(
        booking.club_id, sport=booking.sport, start=booking.start
    )


async def _loaded(bookings: BookingRepository, booking_id: UUID) -> Booking:
    return invariant(await bookings.load(booking_id), f"no booking {booking_id}")
