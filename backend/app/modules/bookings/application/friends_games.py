"""**A friends game: booked at send, its invited seats answered, called off by
its sender** (#751; ``docs/adr/0202`` §5–§6; the friends mechanics §8.2, §9,
§11.2).

Five acts on one booking, each in its caller's transaction — the proposals'
send, answer and call-off, which take the booking's row first — and **nothing
here commits**:

- **booked** — the Booking's second birth, under an id of its own: the court
  held on its hour's unique index (``CourtTaken`` on a race), and the ordinary
  Game opened with **only the sender seated**, every other seat open for its
  invited friend — so its room, whose members are the line-up, has the sender
  in it from the send;
- **accepted** — the friend is In on the booking and seated on the Game, on the
  side the card drew them, and joins the room by the same act;
- **declined** and **run out** — the seat is empty; the Game's seat stays open;
- **called off** — the sender's, before the cut-off: the booking off, the court
  the club's again (the partial index), the Game called off whole by nobody and
  its room with it;
- **invited into an empty seat** (#752) — a friend of anybody In, the seat
  theirs to accept until their 24 hours end, unless somebody takes it first —
  and accepted, seated on that seat's side;
- **opened to the group** (#752) — the sender's, before the cut-off, and the
  cut-off's own for every seat still empty on a game the sender covers;
- **the cover warning** (#752) — recorded once, a day before the cut-off.

Leaving is the ordinary ``LeaveTheBooking``: what becomes of the seat is the
booking's fold to say.

Whether the act may be done — whose seat, whose week, whose money — is the
caller's question, asked before this.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.engines.matchfit.core import SearchMode
from app.kernel import Instant, Sport, invariant
from app.modules.bookings.domain.booking import BookedCourt, Booking, PayMode
from app.modules.bookings.domain.ports import (
    BookingRepository,
    GameChanges,
    GameOpening,
)


@final
@dataclass(frozen=True, slots=True)
class FriendsGameToBook:
    """A friends game being sent: everything its booking is born with."""

    booking_id: UUID
    pool_id: UUID
    club_id: UUID
    sport: Sport
    kind: SearchMode
    start: Instant
    share_grosze: int
    sender: UUID
    #: The sides the card drew, the sender on one.
    first_side: tuple[UUID, ...]
    second_side: tuple[UUID, ...]
    pay_mode: PayMode
    court: BookedCourt
    cut_off: Instant


@final
class FriendsGames:
    def __init__(
        self,
        *,
        bookings: BookingRepository,
        opening: GameOpening,
        games: GameChanges,
    ) -> None:
        self._bookings = bookings
        self._opening = opening
        self._games = games

    async def book(self, game: FriendsGameToBook, *, at: Instant) -> Booking:
        """Book it, and open its Game with only the sender on the court."""

        def seated(side: tuple[UUID, ...]) -> tuple[UUID | None, ...]:
            return tuple(p if p == game.sender else None for p in side)

        game_id = await self._opening.open(
            booking_id=game.booking_id,
            sport=game.sport,
            counted=game.kind is SearchMode.COMPETITIVE,
            first_side=seated(game.first_side),
            second_side=seated(game.second_side),
            starts_at=game.start,
            at=at,
        )
        booking = Booking.booked_by_a_friend(
            booking_id=game.booking_id,
            pool_id=game.pool_id,
            club_id=game.club_id,
            court=game.court,
            sport=game.sport,
            kind=game.kind,
            start=game.start,
            share_grosze=game.share_grosze,
            sender=game.sender,
            first_side=game.first_side,
            second_side=game.second_side,
            pay_mode=game.pay_mode,
            cut_off=game.cut_off,
            game_id=game_id,
            at=at,
        )
        await self._bookings.save(booking)
        return booking

    async def accept(
        self, booking_id: UUID, player_id: UUID, *, at: Instant
    ) -> Booking:
        """The friend is In: on the booking, and seated on its Game."""

        booking = await _loaded(self._bookings, booking_id)
        seat = booking.invitation_of(player_id)
        invariant(seat is not None, f"{player_id} was never invited to {booking_id}")
        assert seat is not None
        booking.accept(player_id, at=at)
        await self._bookings.save(booking)
        await self._games.seat(booking_id, player_id, side=seat.side, at=at)
        return booking

    async def decline(self, booking_id: UUID, player_id: UUID, *, at: Instant) -> bool:
        """Whether anything was recorded — nothing for a seat no longer
        waiting."""

        booking = await _loaded(self._bookings, booking_id)
        declined = booking.decline(player_id, at=at)
        await self._bookings.save(booking)
        return declined

    async def run_out(self, booking_id: UUID, *, at: Instant) -> tuple[UUID, ...]:
        """Every invitation on this game whose time is up, run out: answers
        whose."""

        booking = await _loaded(self._bookings, booking_id)
        ran_out = tuple(
            seat.player_id
            for seat in booking.to_run_out(at)
            if booking.invited_seat_ran_out(seat.player_id, at=at)
        )
        await self._bookings.save(booking)
        return ran_out

    async def invite(
        self,
        booking_id: UUID,
        player_id: UUID,
        *,
        by: UUID,
        seat_of: UUID,
        at: Instant,
    ) -> Booking:
        """The friend invited into the empty seat named ``seat_of``."""

        booking = await _loaded(self._bookings, booking_id)
        booking.invite(player_id, by=by, seat_of=seat_of, at=at)
        await self._bookings.save(booking)
        return booking

    async def open(self, booking_id: UUID, seat_of: UUID, *, at: Instant) -> Booking:
        """The empty seat named ``seat_of`` put to the group: a rescue."""

        booking = await _loaded(self._bookings, booking_id)
        booking.open_to_the_group(seat_of, at=at)
        await self._bookings.save(booking)
        return booking

    async def open_at_the_cut_off(
        self, booking_id: UUID, *, at: Instant
    ) -> tuple[UUID, ...]:
        """Every seat still empty at the cut-off, opened: answers whose they
        were."""

        booking = await _loaded(self._bookings, booking_id)
        opened = booking.open_at_the_cut_off(at=at)
        await self._bookings.save(booking)
        return opened

    async def warn(self, booking_id: UUID, *, at: Instant) -> bool:
        """The cover warning, recorded if it is due."""

        booking = await _loaded(self._bookings, booking_id)
        if not booking.warn_the_cover(at=at):
            return False
        await self._bookings.save(booking)
        return True

    async def call_off(self, booking_id: UUID, *, at: Instant) -> Booking:
        """The sender calls it off: the court the club's again, the Game and its
        room ended."""

        booking = await _loaded(self._bookings, booking_id)
        booking.call_off_by_the_sender(at=at)
        await self._bookings.save(booking)
        await self._games.call_off_whole(booking_id, at=at)
        return booking


async def _loaded(bookings: BookingRepository, booking_id: UUID) -> Booking:
    booking = await bookings.load(booking_id)
    invariant(booking is not None, f"no booking {booking_id}")
    assert booking is not None
    return booking


__all__ = ["FriendsGameToBook", "FriendsGames"]
