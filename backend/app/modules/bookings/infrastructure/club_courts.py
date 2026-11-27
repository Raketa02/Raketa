"""What Bookings asks of the Club context, and what it answers for it — both
over the Club context's own published ports, so the arrow runs
``bookings → clubs`` only.

**The first free court** is read off what the club sells, as it stood **before
any deadline**: a card keeps the book-by it was made with, so a club that has
lengthened its release lead since has not taken a full game's court away — the same
reading ``proposals``' ``held`` makes of a card's court hour. The courts come in
the club's own order, and the first of the sport at the hour is the one booked.

**The court hours bookings hold** are what a club can no longer sell, and why a
court with a booking ahead cannot be deleted or its hour closed
(``CourtBookings``).

**The court a club's cancel took a game off is closed for the hour** (#673)
through the Club context's own act, an exception on the club's list worded by
the cancel's reason — the desk reads why, and removes it to sell the court
again.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import timedelta
from typing import Final, final
from uuid import UUID

from app.kernel import Instant, Sport
from app.modules.bookings.domain.booking import BookedCourt, CancelReason, FreeCourt
from app.modules.bookings.domain.ports import BookingDirectory, CourtForTheGame
from app.modules.clubs.application.hours_exceptions import CloseACourtForAnHour
from app.modules.clubs.domain.ports import SellableCourtHours, TakenCourtHour
from app.modules.clubs.domain.rakieta_terms import before_any_deadline
from app.modules.clubs.domain.sellable import ClubOffer

#: Every game is one hour, for every sport (the mechanics §2).
_A_GAME: Final = timedelta(hours=1)

#: The reason a court a club's cancel closed gives on the club's own list of
#: exceptions — *Game cancelled · repair* — by the cancel's reason (#673). No
#: player reads it.
_CLOSED_BY_A_CANCEL: Final[dict[CancelReason, str]] = {
    CancelReason.WEATHER: "Game cancelled · weather",
    CancelReason.REPAIR: "Game cancelled · repair",
    CancelReason.DOUBLE_BOOKING: "Game cancelled · booked twice",
    CancelReason.OTHER: "Game cancelled",
}


@final
class SellableClubCourts:
    """``ClubCourtsAtTheHour`` over ``SellableCourtHours``."""

    def __init__(self, sellable: SellableCourtHours) -> None:
        self._sellable = sellable

    async def first_free(
        self, club_id: UUID, *, sport: Sport, start: Instant
    ) -> CourtForTheGame | None:
        offer = await self._offer(club_id, start=start)
        courts = () if offer is None else _courts(offer, sport=sport, start=start)
        if offer is None or not courts:
            return None
        return CourtForTheGame(
            court=courts[0].court,
            cut_off_hours=offer.settings.cut_off_hours,
        )

    async def free_courts(
        self, club_id: UUID, *, sport: Sport, start: Instant
    ) -> Sequence[FreeCourt]:
        offer = await self._offer(club_id, start=start)
        return () if offer is None else _courts(offer, sport=sport, start=start)

    async def _offer(self, club_id: UUID, *, start: Instant) -> ClubOffer | None:
        return (
            await self._sellable.between(
                [club_id],
                start=start,
                end=start + _A_GAME,
                now=before_any_deadline(start),
            )
        ).get(club_id)


def _courts(offer: ClubOffer, *, sport: Sport, start: Instant) -> tuple[FreeCourt, ...]:
    """The courts of ``sport`` on sale from ``start``, in the club's order,
    each with its kind (#671) and its share at the hour (#672)."""

    return tuple(
        FreeCourt(
            court=BookedCourt(
                court_id=hour.court_id, name=hour.court_name, indoor=hour.indoor
            ),
            share_grosze=hour.share_grosze,
        )
        for hour in offer.hours
        if hour.sport is sport and hour.start == start
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


@final
class ClosedByTheCancel:
    """The Bookings context's ``CourtClosures``, over the Club context's own
    act — an exception closing the one court for the one hour."""

    def __init__(self, close: CloseACourtForAnHour) -> None:
        self._close = close

    async def close(
        self,
        club_id: UUID,
        court_id: UUID,
        *,
        start: Instant,
        because: CancelReason,
        at: Instant,
    ) -> None:
        await self._close.execute(
            club_id, court_id, start=start, reason=_CLOSED_BY_A_CANCEL[because], at=at
        )
