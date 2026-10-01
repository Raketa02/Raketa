"""What the Bookings context needs, in its own words.

**Two ports are its own store**: the Booking repository, whose ``save`` writes
the ``bookings`` and ``booking_seats`` projections in the caller's transaction,
and the directory that reads them back — which court hours bookings hold, and
which games a player has booked.

**Two are demands on contexts it does not write**: which courts a club still
has for Raketa at an hour, and its cut-off (``clubs``, over what it sells), and
the ordinary Game a booking opens (``games``, over the use case a completed
line-up opens one with).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol, final, runtime_checkable
from uuid import UUID

from app.kernel import Instant, Sport
from app.modules.bookings.domain.booking import BookedCourt, Booking


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
        """When each of this player's booked games starts, from ``start`` until
        ``end`` — for ever when ``end`` is ``None`` — soonest first."""
        ...


@final
@dataclass(frozen=True, slots=True)
class CourtForTheGame:
    """The court a full game is booked on — **the first free court of its
    sport at its hour**, in the club's own order (the mechanics §11.2) — and
    how many hours before the game the club's free cancellation ends."""

    court: BookedCourt
    cut_off_hours: int


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
