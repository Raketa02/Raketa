"""Booking a full game: the court, then the Booking and the Game it opens
(the mechanics §11; ``docs/adr/0189`` §5).

**Two acts the fill asks for, in its own transaction**: the court first —
*which* court is the booking's decision, the first free one of the sport at the
hour — and, once every seat's money is held, the booking itself, which opens
the ordinary Game exactly as a completed line-up does. **Nothing here commits**:
the fill's boundary is the yes that filled it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.engines.matchfit.core import SearchMode
from app.kernel import Instant, Minutes, Sport, hours, minutes, shifted
from app.modules.bookings.domain.booking import BookedCourt, Booking
from app.modules.bookings.domain.ports import (
    BookingRepository,
    ClubCourtsAtTheHour,
    GameOpening,
)


@final
@dataclass(frozen=True, slots=True)
class CourtOffered:
    """The court a full game would be booked on, the moment its free
    cancellation ends, and how long an On request club has to answer."""

    court: BookedCourt
    cut_off: Instant
    time_to_confirm: Minutes


@final
class FindACourt:
    def __init__(self, *, courts: ClubCourtsAtTheHour) -> None:
        self._courts = courts

    async def execute(
        self, club_id: UUID, *, sport: Sport, start: Instant
    ) -> CourtOffered | None:
        found = await self._courts.first_free(club_id, sport=sport, start=start)
        if found is None:
            return None
        # Elapsed hours, as the card's *no free cancellation* reads them.
        return CourtOffered(
            court=found.court,
            cut_off=shifted(start, hours(-found.cut_off_hours)),
            time_to_confirm=minutes(found.time_to_confirm_minutes),
        )


@final
@dataclass(frozen=True, slots=True)
class GameToBook:
    """A full game, its seats paid: everything its booking is born with."""

    #: The proposal's id, which the booking takes.
    booking_id: UUID
    pool_id: UUID
    club_id: UUID
    sport: Sport
    kind: SearchMode
    start: Instant
    share_grosze: int
    first_side: tuple[UUID, ...]
    second_side: tuple[UUID, ...]
    court: BookedCourt
    cut_off: Instant


@final
class BookTheGame:
    def __init__(self, *, bookings: BookingRepository, games: GameOpening) -> None:
        self._bookings = bookings
        self._games = games

    async def execute(self, game: GameToBook, *, at: Instant) -> Booking:
        game_id = await self._games.open(
            booking_id=game.booking_id,
            sport=game.sport,
            counted=game.kind is SearchMode.COMPETITIVE,
            first_side=game.first_side,
            second_side=game.second_side,
            starts_at=game.start,
            at=at,
        )
        booking = Booking.confirmed(
            booking_id=game.booking_id,
            pool_id=game.pool_id,
            club_id=game.club_id,
            court=game.court,
            sport=game.sport,
            kind=game.kind,
            start=game.start,
            share_grosze=game.share_grosze,
            first_side=game.first_side,
            second_side=game.second_side,
            cut_off=game.cut_off,
            game_id=game_id,
            at=at,
        )
        await self._bookings.save(booking)
        return booking
