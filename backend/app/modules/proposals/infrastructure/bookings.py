"""The two facts that pass between proposals and bookings, both answered by
adapters **signed here**, so the arrow runs ``proposals → bookings`` only (#541).

``BookingsGameBookings`` is the fill's demand — a court for a full game, and the
booking that opens its Game — over the Bookings context's own use cases.
``BookingsBookedGames`` answers *games per week* and *one game per hour* — the
deck's, the proposer's and the fill's — with a player's booked games, replacing
the stand-in that answered nothing while no game could be booked.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import final
from uuid import UUID

from app.kernel import Instant, Sport
from app.modules.bookings.application.book_the_game import (
    BookTheGame,
    FindACourt,
    GameToBook,
)
from app.modules.bookings.domain.booking import BookedCourt
from app.modules.bookings.domain.errors import CourtTaken
from app.modules.bookings.domain.ports import BookingDirectory
from app.modules.proposals.domain.errors import CourtJustTaken
from app.modules.proposals.domain.ports import BookableCourt, FullGame


@final
class BookingsGameBookings:
    def __init__(self, *, find: FindACourt, book: BookTheGame) -> None:
        self._find = find
        self._book = book

    async def court_for(
        self, club_id: UUID, *, sport: Sport, start: Instant
    ) -> BookableCourt | None:
        offered = await self._find.execute(club_id, sport=sport, start=start)
        if offered is None:
            return None
        return BookableCourt(
            court_id=offered.court.court_id,
            name=offered.court.name,
            cut_off=offered.cut_off,
        )

    async def book(self, game: FullGame, *, at: Instant) -> UUID:
        try:
            return await self._booked(game, at=at)
        except CourtTaken as taken:
            raise CourtJustTaken() from taken

    async def _booked(self, game: FullGame, *, at: Instant) -> UUID:
        booking = await self._book.execute(
            GameToBook(
                booking_id=game.proposal_id,
                pool_id=game.pool_id,
                club_id=game.club_id,
                sport=game.sport,
                kind=game.kind,
                start=game.start,
                share_grosze=game.share_grosze,
                first_side=game.first_side,
                second_side=game.second_side,
                court=BookedCourt(court_id=game.court.court_id, name=game.court.name),
                cut_off=game.court.cut_off,
            ),
            at=at,
        )
        return booking.game_id


@final
class BookingsBookedGames:
    def __init__(self, directory: BookingDirectory) -> None:
        self._directory = directory

    async def starts_of(
        self, player_id: UUID, *, start: Instant, end: Instant
    ) -> Sequence[Instant]:
        return await self._directory.starts_for(player_id, start=start, end=end)
