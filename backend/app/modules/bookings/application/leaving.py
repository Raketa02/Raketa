"""Leaving a booked game, and the cut-off (#544; the mechanics §12.3, §13,
§16.12; ``docs/adr/0189`` §5).

**Acts on one booking, each in its caller's transaction**, which is the
proposal's — the leaver's, and the cut-off job's — and **nothing here
commits**:

- **left** — the leaver's seat opens on the booking and on its Game, whose
  room they leave with it; what it costs them is the money's, decided by the
  caller;
- **a card not fixed in time** (#639) — a player whose holding was refused
  lets their seat go when their time to fix the card runs out, as a leaver;
- **called off at the cut-off** — a seat that opened before the club's cut-off
  is still open at it: the game is off, the court the club's again, its Game
  and room end, and the club's desk is emailed at once. The people still in are
  answered, for the caller to refund in full.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.application.ports.mail import MailQueue
from app.kernel import Instant, invariant
from app.modules.bookings.application.request_emails import (
    called_off_at_the_cut_off_email,
)
from app.modules.bookings.domain.booking import Booking
from app.modules.bookings.domain.ports import BookingRepository, ClubDesks, GameChanges


@final
class LeaveTheBooking:
    """*Leave the game*: whether it may still be left is the caller's
    question, asked before this."""

    def __init__(self, *, bookings: BookingRepository, games: GameChanges) -> None:
        self._bookings = bookings
        self._games = games

    async def execute(self, booking_id: UUID, player_id: UUID, *, at: Instant) -> None:
        booking = await _loaded(self._bookings, booking_id)
        booking.leave(player_id, at=at)
        await self._bookings.save(booking)
        await self._games.vacate(booking_id, player_id, at=at)


@final
class TimeToFixTheCard:
    """**A player's holding was refused** (#639; the mechanics Q113): the game
    stays booked while they have their time to fix the card. Fixed in time,
    their seat is simply theirs again; run out, it opens as a leaver's does —
    the Game's seat vacated, so they leave its room — and the money's part is
    the caller's."""

    def __init__(self, *, bookings: BookingRepository, games: GameChanges) -> None:
        self._bookings = bookings
        self._games = games

    async def give(
        self,
        booking_id: UUID,
        player_id: UUID,
        *,
        until: Instant,
        seat_charge_id: UUID,
        reason: str,
        at: Instant,
    ) -> None:
        booking = await _loaded(self._bookings, booking_id)
        booking.card_to_fix(
            player_id,
            until=until,
            seat_charge_id=seat_charge_id,
            reason=reason,
            at=at,
        )
        await self._bookings.save(booking)

    async def fixed(self, booking_id: UUID, player_id: UUID, *, at: Instant) -> bool:
        booking = await _loaded(self._bookings, booking_id)
        if not booking.card_fixed(player_id, at=at):
            return False
        await self._bookings.save(booking)
        return True

    async def not_fixed(
        self, booking_id: UUID, player_id: UUID, *, at: Instant
    ) -> bool:
        booking = await _loaded(self._bookings, booking_id)
        if not booking.card_not_fixed(player_id, at=at):
            return False
        await self._bookings.save(booking)
        await self._games.vacate(booking_id, player_id, at=at)
        return True


@final
class CallOffAtTheCutOff:
    """The cut-off's act on one booking."""

    def __init__(
        self,
        *,
        bookings: BookingRepository,
        games: GameChanges,
        desks: ClubDesks,
        mail: MailQueue,
        bookings_page: str,
    ) -> None:
        self._bookings = bookings
        self._games = games
        self._desks = desks
        self._mail = mail
        self._bookings_page = bookings_page

    async def execute(
        self, booking_id: UUID, *, at: Instant
    ) -> tuple[UUID, ...] | None:
        """Everybody still in — or ``None`` for a booking not short at its
        cut-off at ``at``, which records nothing."""

        booking = await _loaded(self._bookings, booking_id)
        if not booking.short_at_the_cut_off(now=at):
            return None
        booking.call_off_at_the_cut_off(at=at)
        await self._bookings.save(booking)
        await self._games.call_off(booking_id, at=at)
        desk = await self._desks.of(booking.club_id)
        if desk is not None:
            await self._mail.enqueue(
                called_off_at_the_cut_off_email(
                    to=desk.email,
                    club=desk.club_name,
                    court=booking.court.name,
                    sport=booking.sport,
                    starts_at=booking.start,
                    hour_still_ahead=at < booking.start,
                    link=self._bookings_page,
                ),
                at=at,
            )
        return booking.players


async def _loaded(bookings: BookingRepository, booking_id: UUID) -> Booking:
    return invariant(await bookings.load(booking_id), f"no booking {booking_id}")
