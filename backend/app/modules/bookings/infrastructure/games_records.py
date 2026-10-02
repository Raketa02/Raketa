"""What passes between a booking and its ordinary Game after the fill, both
ways round the one arrow ``bookings → games`` (#547).

``BookingCheckIns`` **signs the Games context's demand** ``ClubCheckIns``: who
the club's desk checked in, read off the booking's stream — a booked game's
``challenge_id`` is its booking's id — so a player the club saw arrive is never
reported as not turning up, and the scan has one home.

``GameNoShowsOnTheRecord`` **answers this context's own demand** ``GameNoShows``
over the Games context's repository: who a report of not turning up stood
against, folded by the Game's own rule — so *keeps plans* breaks a booked game
on the record of somebody who did not come, and never re-decides it here.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.kernel import Instant
from app.modules.bookings.domain.ports import BookingRepository
from app.modules.games.domain.ports import GameRepository


@final
class BookingCheckIns:
    """``games``' ``ClubCheckIns`` over the booking streams."""

    def __init__(self, bookings: BookingRepository) -> None:
        self._bookings = bookings

    async def checked_in(self, challenge_id: UUID) -> frozenset[UUID]:
        # A booked game's challenge id is its booking's.
        booking = await self._bookings.load(challenge_id)
        return frozenset() if booking is None else frozenset(booking.checked_in)


@final
class GameNoShowsOnTheRecord:
    """``GameNoShows`` over the Games context's own aggregate."""

    def __init__(self, games: GameRepository) -> None:
        self._games = games

    async def did_not_come(self, booking_id: UUID, *, now: Instant) -> frozenset[UUID]:
        game = await self._games.for_challenge(booking_id)
        return frozenset() if game is None else game.confirmed_no_shows_at(now)
