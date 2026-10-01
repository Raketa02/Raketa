"""What the Bookings context needs, in its own words.

**Two ports are its own store**: the Booking repository, whose ``save`` writes
the ``bookings`` and ``booking_seats`` projections in the caller's transaction,
and the directory that reads them back — which court hours bookings hold, which
games a player has booked, and how many were booked in each pool. **A third is
its own key**: each seat's check-in code, derived under the server's secret
(#542).

**Three are demands on contexts it does not write**: which courts a club still
has for Raketa at an hour, its cut-off and its time to confirm (``clubs``, over
what it sells); the ordinary Game a booking opens (``games``, over the use case
a completed line-up opens one with); and, for an On request club, whom to tell
that a game waits for its answer and what the club is called (``clubs``, over
its own account and details — #543).
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol, final, runtime_checkable
from uuid import UUID

from app.kernel import Instant, Sport
from app.modules.bookings.domain.booking import BookedCourt, Booking
from app.modules.bookings.domain.check_in import CheckInCode


@runtime_checkable
class BookingRepository(Protocol):
    async def load(self, booking_id: UUID) -> Booking | None: ...

    async def save(self, booking: Booking) -> None:
        """Append what the booking recorded and write its rows, in the caller's
        transaction."""
        ...


@final
@dataclass(frozen=True, slots=True)
class HeldCourtHour:
    """A court hour a booking holds."""

    court_id: UUID
    start: Instant
    booking_id: UUID


@runtime_checkable
class BookingDirectory(Protocol):
    """The projections, read. Written only by ``BookingRepository.save``."""

    async def held_at(
        self, club_id: UUID, *, start: Instant, end: Instant | None
    ) -> Sequence[HeldCourtHour]:
        """Every court hour of this club a booking holds, starting at or after
        ``start`` and before ``end`` — for ever when ``end`` is ``None``."""
        ...

    async def starts_for(
        self, player_id: UUID, *, start: Instant, end: Instant | None
    ) -> Sequence[Instant]:
        """When each of this player's **booked** games starts, from ``start``
        until ``end`` — for ever when ``end`` is ``None`` — soonest first. A game
        still waiting for its club is not booked yet, and one called off never
        will be."""
        ...

    async def of_player(self, player_id: UUID) -> Sequence[UUID]:
        """Every booking this player has a seat on, whenever it is and whatever
        it came to — **soonest game first**, and by id among games at one hour
        (#542)."""
        ...

    async def counted_in(self, pool_ids: Collection[UUID]) -> Mapping[UUID, int]:
        """How many games were booked in each of these pools — one question
        about the set. A pool absent from the answer has booked none (#542).

        **Only a booked game counts**: one waiting for its club, or called off,
        is not a game anybody will play there (#543; #544 and #547 leave theirs
        out the same way)."""
        ...

    async def waiting_at(self, club_id: UUID) -> Sequence[UUID]:
        """Every booking at this club waiting for its answer — **the one due
        first, first** (#543)."""
        ...

    async def unanswered(self, *, now: Instant) -> Sequence[UUID]:
        """Every booking still waiting for its club whose answer was due by
        ``now``, the longest overdue first — **candidates**: the aggregate
        decides."""
        ...


@runtime_checkable
class CheckInCodes(Protocol):
    """Each seat's check-in code (the mechanics §15.1): derived from the
    booking and the player under **the server's own key**, never stored, so
    the phone is shown it and the desk recomputes it."""

    def code_for(self, booking_id: UUID, player_id: UUID) -> CheckInCode: ...


@final
@dataclass(frozen=True, slots=True)
class CourtForTheGame:
    """The court a full game is booked on — **the first free court of its
    sport at its hour**, in the club's own order (the mechanics §11.2) — how
    many hours before the game the club's free cancellation ends, and how many
    minutes an On request club has to answer."""

    court: BookedCourt
    cut_off_hours: int
    time_to_confirm_minutes: int


@runtime_checkable
class ClubCourtsAtTheHour(Protocol):
    """**A demand of the Club context**: the courts a club still has for Raketa
    at an hour."""

    async def first_free(
        self, club_id: UUID, *, sport: Sport, start: Instant
    ) -> CourtForTheGame | None:
        """The first court of ``sport`` the club still has for Raketa from
        ``start`` — **whatever deadline its settings now give the hour**, since
        a card keeps the book-by it was made with — and its cut-off. ``None``
        when every court of the sport then is booked, closed or no longer
        offered, or the club no longer sells."""
        ...


@runtime_checkable
class GameOpening(Protocol):
    """**A demand of the Games context**: the ordinary Game a booking opens,
    exactly as a completed line-up opens one (``docs/adr/0189`` §5, Q6)."""

    async def open(
        self,
        *,
        booking_id: UUID,
        sport: Sport,
        counted: bool,
        first_side: tuple[UUID, ...],
        second_side: tuple[UUID, ...],
        starts_at: Instant,
        at: Instant,
    ) -> UUID:
        """Open the game, in the caller's transaction, and answer its id."""
        ...


@final
@dataclass(frozen=True, slots=True)
class ClubDesk:
    """Whom an email to a club is addressed to — its one sign-in — and what the
    club is called."""

    email: str
    club_name: str


@runtime_checkable
class ClubDesks(Protocol):
    """**A demand of the Club context**: the desk a request is sent to (the
    mechanics §16.12 — *a request is waiting for you*, at once)."""

    async def of(self, club_id: UUID) -> ClubDesk | None:
        """The club's desk, or ``None`` for a club that no longer exists."""
        ...
