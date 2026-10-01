"""What Bookings asks of the Club context, and what it answers for it — both
over the Club context's own published ports, so the arrow runs
``bookings → clubs`` only.

**The first free court** is read off what the club sells, as it stood **before
any deadline**: a card keeps the book-by it was made with, so a club that has
lengthened its notice since has not taken a full game's court away — the same
reading ``proposals``' ``held`` makes of a card's court hour. The courts come in
the club's own order, and the first of the sport at the hour is the one booked.

**The court hours bookings hold** are what a club can no longer sell, and why a
court with a booking ahead cannot be deleted or its hour closed
(``CourtBookings``).
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import timedelta
from typing import Final, final
from uuid import UUID

from app.kernel import Instant, Sport
from app.modules.bookings.domain.booking import BookedCourt
from app.modules.bookings.domain.ports import BookingDirectory, CourtForTheGame
from app.modules.clubs.domain.ports import SellableCourtHours, TakenCourtHour
from app.modules.clubs.domain.raketa_terms import before_any_deadline

#: Every game is one hour, for every sport (the mechanics §2).
_A_GAME: Final = timedelta(hours=1)


@final
class SellableClubCourts:
    """``ClubCourtsAtTheHour`` over ``SellableCourtHours``."""

    def __init__(self, sellable: SellableCourtHours) -> None:
        self._sellable = sellable

    async def first_free(
        self, club_id: UUID, *, sport: Sport, start: Instant
    ) -> CourtForTheGame | None:
        offer = (
            await self._sellable.between(
                [club_id],
                start=start,
                end=start + _A_GAME,
                now=before_any_deadline(start),
            )
        ).get(club_id)
        if offer is None:
            return None
        court = next(
            (
                hour
                for hour in offer.hours
                if hour.sport is sport and hour.start == start
            ),
            None,
        )
        if court is None:
            return None
        return CourtForTheGame(
            court=BookedCourt(court_id=court.court_id, name=court.court_name),
            cut_off_hours=offer.settings.cut_off_hours,
        )


@final
class BookedCourtHours:
    """The Club context's ``CourtBookings``, over the bookings' own directory."""

    def __init__(self, directory: BookingDirectory) -> None:
        self._directory = directory

    async def taken(
        self, club_id: UUID, *, start: Instant, end: Instant | None = None
    ) -> Sequence[TakenCourtHour]:
        return [
            TakenCourtHour(
                court_id=held.court_id, start=held.start, booking_id=held.booking_id
            )
            for held in await self._directory.held_at(club_id, start=start, end=end)
        ]
