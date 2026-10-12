"""``GameClubs``, the Games context's demand, answered by Bookings (#657;
``docs/adr/0195`` §3).

**The Game does not know its club; its booking does.** So where a booked game
is played is read here — the booking's club, then that club's point off what the
Club context publishes (``ClubDirectory``) — on the ``bookings`` side of the
arrow, which ``games`` may not cross. **The distance is the platform's one
great-circle distance** (``matchmaking/domain/geography.py``'s ``distance_km``),
the function every distance on the platform is read with; a second spelling of
it here would be a second opinion about how far apart two places are.

**A position asked about is measured and dropped**: it is never logged,
stored or carried past the answer.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.modules.bookings.domain.ports import BookingRepository
from app.modules.clubs.domain.ports import ClubDirectory
from app.modules.games.domain.ports import FromTheClub, GameClub
from app.modules.matchmaking.domain.geography import Point, distance_km

_METRES_PER_KILOMETRE = 1_000.0


@final
class BookedGameClubs:
    """``GameClubs`` over the booking's stream and the Club directory."""

    def __init__(self, *, bookings: BookingRepository, clubs: ClubDirectory) -> None:
        self._bookings = bookings
        self._clubs = clubs

    async def of(self, booking_id: UUID) -> GameClub | None:
        booking = await self._bookings.load(booking_id)
        if booking is None:
            return None
        listing = (await self._clubs.listed([booking.club_id])).get(booking.club_id)
        if listing is None:
            return None
        return GameClub(
            name=listing.name, latitude=listing.latitude, longitude=listing.longitude
        )

    async def metres_from(
        self, booking_id: UUID, *, latitude: float, longitude: float
    ) -> FromTheClub | None:
        club = await self.of(booking_id)
        if club is None:
            return None
        kilometres = distance_km(
            Point(latitude=latitude, longitude=longitude),
            Point(latitude=club.latitude, longitude=club.longitude),
        )
        return FromTheClub(
            club_name=club.name, metres=kilometres * _METRES_PER_KILOMETRE
        )
