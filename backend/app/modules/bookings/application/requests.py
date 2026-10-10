"""A full game at an On request club, put to the club and answered (#543; the
mechanics §16.3, §16.8, §13; ``docs/adr/0189`` §3, §5).

**Four acts on one booking, each in its caller's transaction**, which is the
proposal's — a request is the fill's, an answer the club's, and a withdrawal
whoever's seat opened — and **nothing here commits**:

- **asked** — the booking is born *waiting for the club*, the court reserved for it,
  or the same game is asked again once full again; and the club's desk is
  emailed at once, since its window is short;
- **accepted** — the ordinary Game opens, exactly as a booked game's does, and
  the booking is booked; the money is the caller's, taken before this;
- **turned down** — refused, or not answered in time: called off, nobody paid,
  and each player emailed which it was (#623; Q105);
- **withdrawn** — seats opened while it waited: nobody paid, nobody keeps a seat
  on it, and the game is filling again.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.application.ports.mail import MailQueue
from app.engines.matchfit.core import SearchMode
from app.kernel import Instant, Sport, invariant
from app.modules.bookings.application.request_emails import (
    club_turned_it_down_email,
    request_waiting_email,
)
from app.modules.bookings.domain.booking import BookedCourt, Booking
from app.modules.bookings.domain.ports import (
    BookingRepository,
    ClubDesks,
    GameOpening,
    PlayerAddresses,
)


@final
@dataclass(frozen=True, slots=True)
class GameToRequest:
    """A full game at an On request club: everything its request holds."""

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
    #: The court reserved for the club's answer.
    court: BookedCourt
    cut_off: Instant
    answer_by: Instant
    #: The player whose own act put it to the club — ``None`` when nobody's did.
    filled_by: UUID | None


@final
class RequestTheGame:
    def __init__(
        self,
        *,
        bookings: BookingRepository,
        desks: ClubDesks,
        mail: MailQueue,
        answer_page: str,
    ) -> None:
        self._bookings = bookings
        self._desks = desks
        self._mail = mail
        self._answer_page = answer_page

    async def execute(self, game: GameToRequest, *, at: Instant) -> Booking:
        """Ask the club, holding the court — ``CourtTaken`` when another game
        claimed it a moment before, as a booking's claim is refused."""

        booking = await self._bookings.load(game.booking_id)
        if booking is None:
            booking = Booking.requested(
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
                answer_by=game.answer_by,
                filled_by=game.filled_by,
                at=at,
            )
        else:
            booking.request_again(
                court=game.court,
                first_side=game.first_side,
                second_side=game.second_side,
                cut_off=game.cut_off,
                answer_by=game.answer_by,
                filled_by=game.filled_by,
                at=at,
            )
        await self._bookings.save(booking)
        desk = await self._desks.of(game.club_id)
        if desk is not None:
            await self._mail.enqueue(
                request_waiting_email(
                    to=desk.email,
                    club=desk.club_name,
                    court=game.court.name,
                    sport=game.sport,
                    starts_at=game.start,
                    share_grosze=game.share_grosze,
                    answer_by=game.answer_by,
                    link=self._answer_page,
                ),
                at=at,
            )
        return booking


@final
class BookTheRequest:
    """The club said yes and every seat is paid: the Game opens and the booking
    is booked. Whether it may be accepted is the caller's question."""

    def __init__(self, *, bookings: BookingRepository, games: GameOpening) -> None:
        self._bookings = bookings
        self._games = games

    async def execute(self, booking_id: UUID, *, at: Instant) -> Booking:
        booking = invariant(
            await self._bookings.load(booking_id), f"no booking {booking_id}"
        )
        game_id = await self._games.open(
            booking_id=booking.booking_id,
            sport=booking.sport,
            counted=booking.kind is SearchMode.COMPETITIVE,
            first_side=booking.first_side,
            second_side=booking.second_side,
            starts_at=booking.start,
            at=at,
        )
        booking.accept(game_id=game_id, at=at)
        await self._bookings.save(booking)
        return booking


@final
class CallOffTheRequest:
    """The club refused it, with its own note — or never answered. **Each
    player on it is emailed which** (#623; the mechanics Q105), in the same
    transaction: no money moves, but while push is off, email is the only way
    to reach a player outside the app."""

    def __init__(
        self,
        *,
        bookings: BookingRepository,
        desks: ClubDesks,
        players: PlayerAddresses,
        mail: MailQueue,
        app_link: str,
    ) -> None:
        self._bookings = bookings
        self._desks = desks
        self._players = players
        self._mail = mail
        self._app_link = app_link

    async def refused(
        self, booking_id: UUID, *, reason: str | None, at: Instant
    ) -> None:
        booking = await self._loaded(booking_id)
        booking.refuse(reason=reason, at=at)
        await self._bookings.save(booking)
        await self._email(booking, refused=True, at=at)

    async def unanswered(self, booking_id: UUID, *, at: Instant) -> None:
        booking = await self._loaded(booking_id)
        booking.time_out(at=at)
        await self._bookings.save(booking)
        await self._email(booking, refused=False, at=at)

    async def _email(self, booking: Booking, *, refused: bool, at: Instant) -> None:
        desk = await self._desks.of(booking.club_id)
        club = "the club" if desk is None else desk.club_name
        addresses = await self._players.of(booking.players)
        for player in booking.players:
            address = addresses.get(player)
            if address is None:
                continue
            await self._mail.enqueue(
                club_turned_it_down_email(
                    to=address.email,
                    club=club,
                    sport=booking.sport,
                    starts_at=booking.start,
                    refused=refused,
                    link=self._app_link,
                ),
                at=at,
            )

    async def _loaded(self, booking_id: UUID) -> Booking:
        return invariant(
            await self._bookings.load(booking_id), f"no booking {booking_id}"
        )


@final
class WithdrawTheRequest:
    """A seat opened on a game waiting for its club."""

    def __init__(self, *, bookings: BookingRepository) -> None:
        self._bookings = bookings

    async def execute(
        self,
        booking_id: UUID,
        *,
        player_ids: tuple[UUID, ...],
        left: tuple[UUID, ...] = (),
        at: Instant,
    ) -> bool:
        """Answers whether a request was withdrawn — nothing for a game that
        never went to its club, or whose club already answered. ``left`` is
        those whose own act took their yes back."""

        booking = await self._bookings.load(booking_id)
        if booking is None or not booking.withdraw_request(
            player_ids, left=left, at=at
        ):
            return False
        await self._bookings.save(booking)
        return True
