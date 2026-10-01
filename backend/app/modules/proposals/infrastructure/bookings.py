"""The facts that pass between proposals and bookings, every one answered by
an adapter **signed here**, so the arrow runs ``proposals → bookings`` only
(#541, #542).

``BookingsGameBookings`` is the fill's demand — a court for a full game, and the
booking that opens its Game — over the Bookings context's own use cases.
``BookingsBookedGames`` answers *games per week* and *one game per hour* — the
deck's, the proposer's and the fill's — with a player's booked games, replacing
the stand-in that answered nothing while no game could be booked.
``BookingsPlayerBookings`` is Home's and the details': a player's booked games
as their bookings record them, folded from each stream, and each seat's
check-in code. ``BookingsGroupBornGames`` is the club's *Games* figure, which
``groups`` asks in its own words: **a group's pool is filed under the group's own
id**, which is this context's fact, so the games booked in a group are the
bookings in its pool.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from typing import final
from uuid import UUID

from app.kernel import Instant, Sport
from app.modules.bookings.application.book_the_game import (
    BookTheGame,
    FindACourt,
    GameToBook,
)
from app.modules.bookings.domain.booking import BookedCourt, Booking
from app.modules.bookings.domain.errors import CourtTaken
from app.modules.bookings.domain.ports import (
    BookingDirectory,
    BookingRepository,
    CheckInCodes,
)
from app.modules.proposals.domain.errors import CourtJustTaken
from app.modules.proposals.domain.home import BookedGame, CheckIn
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


@final
class BookingsPlayerBookings:
    def __init__(
        self,
        *,
        directory: BookingDirectory,
        bookings: BookingRepository,
        codes: CheckInCodes,
    ) -> None:
        self._directory = directory
        self._bookings = bookings
        self._codes = codes

    async def of_player(self, player_id: UUID) -> Sequence[BookedGame]:
        found: list[BookedGame] = []
        for booking_id in await self._directory.of_player(player_id):
            booking = await self._bookings.load(booking_id)
            if booking is not None:
                found.append(_booked_game(booking))
        return found

    async def find(self, booking_id: UUID) -> BookedGame | None:
        booking = await self._bookings.load(booking_id)
        return None if booking is None else _booked_game(booking)

    def check_in(self, booking_id: UUID, player_id: UUID) -> CheckIn:
        code = self._codes.code_for(booking_id, player_id)
        return CheckIn(short_code=code.short_code, qr_payload=code.qr_payload)


def _booked_game(booking: Booking) -> BookedGame:
    return BookedGame(
        booking_id=booking.booking_id,
        pool_id=booking.pool_id,
        club_id=booking.club_id,
        court_name=booking.court.name,
        sport=booking.sport,
        kind=booking.kind,
        start=booking.start,
        share_grosze=booking.share_grosze,
        first_side=booking.first_side,
        second_side=booking.second_side,
        cut_off=booking.cut_off,
        game_id=booking.game_id,
    )


@final
class BookingsGroupBornGames:
    def __init__(self, directory: BookingDirectory) -> None:
        self._directory = directory

    async def born_in(self, group_ids: Collection[UUID]) -> Mapping[UUID, int]:
        return await self._directory.counted_in(group_ids)
