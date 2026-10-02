"""What the club does to its bookings (#547; the mechanics §15.1, §16.7–§16.10,
§16.16; the screens B4, B6).

**Four acts and a read, each in its caller's transaction**, which is the
proposal's — every act on a game locks its proposal's row first — and
**nothing here commits**:

- **the free courts** — every other court of the game's sport the club still
  has for Raketa at its hour, in the club's order: where a game may be moved;
- **moved** — the game is on one of them, and the players read its number;
- **cancelled** — the game is off with the club's reason, its Game and room end
  with it, and everybody it owes money to is answered, for the caller to refund
  in full;
- **checked in** — the desk scanned a player's code on the day;
- **whose code** — what the desk was handed, read: the seat it is, and whether
  it is this club's and today's.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from enum import StrEnum
from typing import Final, final
from uuid import UUID

from app.kernel import Instant, invariant
from app.modules.bookings.domain.booking import BookedCourt, Booking, CancelReason
from app.modules.bookings.domain.check_in import is_the_game_day, read_code
from app.modules.bookings.domain.ports import (
    BookingDirectory,
    BookingRepository,
    CheckInCodes,
    ClubCourtsAtTheHour,
    GameChanges,
)
from app.modules.clubs.domain.court_hours import (
    DAY_CLOSES,
    DAY_OPENS,
    hour_start,
    local_day,
)

#: How far either side of today a typed code is looked for at the desk's club,
#: to say it is another day's — the deck's own horizon, which no booking is
#: further ahead than.
_ANOTHER_DAY_REACH: Final = timedelta(days=14)


@final
class MoveTheBooking:
    def __init__(
        self, *, bookings: BookingRepository, courts: ClubCourtsAtTheHour
    ) -> None:
        self._bookings = bookings
        self._courts = courts

    async def free_courts(self, booking_id: UUID) -> tuple[BookedCourt, ...]:
        """The courts the game may be moved to. The game's own is not among
        them: its booking holds it."""

        booking = await _loaded(self._bookings, booking_id)
        return tuple(
            court
            for court in await self._courts.free_courts(
                booking.club_id, sport=booking.sport, start=booking.start
            )
            if court.court_id != booking.court.court_id
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


@final
class CheckInThePlayer:
    def __init__(self, *, bookings: BookingRepository) -> None:
        self._bookings = bookings

    async def execute(self, booking_id: UUID, player_id: UUID, *, at: Instant) -> None:
        """Whether this player may be checked in — a seat on a booked game, on
        its day, not checked in already — is the caller's question."""

        booking = await _loaded(self._bookings, booking_id)
        booking.check_in(player_id, at=at)
        await self._bookings.save(booking)


class AtTheDesk(StrEnum):
    """What a code handed to a club's desk is, there and then."""

    #: A seat on a game at this club, today.
    HERE_TODAY = "HERE_TODAY"
    #: A seat on a game at this club, on another day.
    ANOTHER_DAY = "ANOTHER_DAY"
    #: A seat on a game at another club.
    ANOTHER_CLUB = "ANOTHER_CLUB"
    #: Nobody's seat.
    UNKNOWN = "UNKNOWN"


@final
@dataclass(frozen=True, slots=True)
class SeatAtTheDesk:
    where: AtTheDesk
    #: The seat it is — ``None`` when it is nobody's.
    booking_id: UUID | None = None
    player_id: UUID | None = None


_NOBODY: Final = SeatAtTheDesk(where=AtTheDesk.UNKNOWN)


@final
class FindTheSeat:
    """Whose seat a code is, as the desk of ``club_id`` reads it at ``now``.

    **A scan names its seat**, so it is checked against the digest and placed.
    **A typed code names nothing**, so it is looked for: among the seats at
    this club today first — the one question a desk asks — then at this club
    on other days, then at other clubs today, so a code for another day or
    another club is told apart from no code at all — another club's code for
    another day is no code a desk can place. Each tier is one read of the
    seats and a digest a seat; only the seat the code is has its stream read.
    Six characters of thirty bits never meet twice at one club on one day.
    """

    def __init__(
        self,
        *,
        bookings: BookingRepository,
        directory: BookingDirectory,
        codes: CheckInCodes,
    ) -> None:
        self._bookings = bookings
        self._directory = directory
        self._codes = codes

    async def execute(self, text: str, *, club_id: UUID, now: Instant) -> SeatAtTheDesk:
        read = read_code(text)
        if read is None:
            return _NOBODY
        if read.booking_id is not None and read.player_id is not None:
            booking = await self._bookings.load(read.booking_id)
            if booking is None or not read.is_of(
                self._codes.code_for(read.booking_id, read.player_id)
            ):
                return _NOBODY
            return _placed(booking, read.player_id, club_id=club_id, now=now)
        today = local_day(now)
        opens, closes = hour_start(today, DAY_OPENS), hour_start(today, DAY_CLOSES)
        here_today = await self._directory.seats_at(club_id, start=opens, end=closes)
        around = await self._directory.seats_at(
            club_id, start=now - _ANOTHER_DAY_REACH, end=now + _ANOTHER_DAY_REACH
        )
        elsewhere = await self._directory.seats_at(None, start=opens, end=closes)
        looked_at, here = set(around), set(here_today)
        for candidates in (
            here_today,
            [seat for seat in around if seat not in here],
            [seat for seat in elsewhere if seat not in looked_at],
        ):
            # A digest a seat, off the projection: a stream is read only for
            # the one seat the code is.
            for booking_id, player_id in candidates:
                if read.is_of(self._codes.code_for(booking_id, player_id)):
                    booking = await self._bookings.load(booking_id)
                    if booking is not None:
                        return _placed(booking, player_id, club_id=club_id, now=now)
        return _NOBODY


def _placed(
    booking: Booking, player_id: UUID, *, club_id: UUID, now: Instant
) -> SeatAtTheDesk:
    if booking.club_id != club_id:
        where = AtTheDesk.ANOTHER_CLUB
    elif not is_the_game_day(booking.start, now=now):
        where = AtTheDesk.ANOTHER_DAY
    else:
        where = AtTheDesk.HERE_TODAY
    return SeatAtTheDesk(
        where=where, booking_id=booking.booking_id, player_id=player_id
    )


async def _loaded(bookings: BookingRepository, booking_id: UUID) -> Booking:
    return invariant(await bookings.load(booking_id), f"no booking {booking_id}")
