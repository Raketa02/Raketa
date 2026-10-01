"""A booked game's details, for a player in it (#542; the mechanics §14.2, §15.1;
the screens A4.1).

**The card and the court facts, folded once.** Who is on which side, read from
the reader's own side; the status and the money line, as Home folds them, against
the same single instant; WHERE — the club, the court the booking was given, and
how far the club is from the reader's Location area — and the hour.

**The forecast is the game's pairing, read where it has always been read**
(``GET /games/{game_id}/pairing``, ``docs/adr/0161``): a booked game is an
ordinary Game, and its balance forecast is the card today's game screen draws
(the screens A4.1: *as built today*). What this read decides is **whether** it is
drawn — while the full game awaits its entry; never while a seat is open.

**On the game's day, the reader's check-in code**: theirs alone, derived and
never stored (``bookings/domain/check_in.py``).

**What leaving would cost, before the reader leaves** (#544; the mechanics §13):
refunded now less the card fee before the cut-off, when somebody takes the seat
after it, nothing paid while the club decides — and no button once the hour
has come. The card fee is the estimate the payments quote.

**The chat is a join, not a field** (``docs/adr/0149`` §3): the reader's rooms,
``GET /conversations``, carry the booked game's room by its ``game_id``.

**Refused with one code** — ``booking_not_found`` — for a booking that does not
exist and one the reader has no seat on, so a booking id says nothing about whose
evening it is.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.kernel import Clock, Instant, Sport, instant
from app.modules.proposals.application.booked_people import people_on
from app.modules.proposals.domain.deck import Sides
from app.modules.proposals.domain.errors import BookingNotFound
from app.modules.proposals.domain.home import (
    BookedGame,
    BookedState,
    CheckIn,
    LeaveTerms,
    check_in_shown,
    leave_terms,
    shows_forecast,
    state_of,
)
from app.modules.proposals.domain.ports import (
    ClubDistances,
    ClubNames,
    DeckPeople,
    DeckPerson,
    GameResults,
    CardFees,
    PlayerBookings,
)


@final
@dataclass(frozen=True, slots=True)
class BookingDetails:
    game: BookedGame
    read_at: Instant
    state: BookedState
    #: The reader's side first, with them first on it.
    sides: Sides
    #: Whether the balance forecast is drawn.
    shows_forecast: bool
    #: The reader's code — on the game's day only.
    check_in: CheckIn | None
    club_name: str | None
    #: ``None`` for a reader with no Location area.
    distance_km: float | None
    people: Mapping[tuple[Sport, UUID], DeckPerson]
    #: What *Leave the game* would cost now — ``None`` where there is no button.
    leaving: LeaveTerms | None = None


@final
class ReadBookingDetails:
    def __init__(
        self,
        *,
        bookings: PlayerBookings,
        results: GameResults,
        people: DeckPeople,
        clubs: ClubNames,
        distances: ClubDistances,
        fees: CardFees,
        clock: Clock,
    ) -> None:
        self._bookings = bookings
        self._results = results
        self._people = people
        self._clubs = clubs
        self._distances = distances
        self._fees = fees
        self._clock = clock

    async def execute(self, booking_id: UUID, reader: UUID) -> BookingDetails:
        now = instant(self._clock.now())
        game = await self._bookings.find(booking_id)
        if game is None or not game.has_a_seat_for(reader):
            raise BookingNotFound()
        result = (
            None
            if game.game_id is None
            else (await self._results.of([game.game_id], reader=reader, now=now)).get(
                game.game_id
            )
        )
        state = state_of(game, result, now=now)
        names = await self._clubs.names_of([game.club_id])
        distances = await self._distances.from_player(reader, [game.club_id])
        return BookingDetails(
            game=game,
            read_at=now,
            state=state,
            sides=game.seen_by(reader),
            shows_forecast=shows_forecast(state.status),
            check_in=(
                self._bookings.check_in(game.booking_id, reader)
                if check_in_shown(state.status, start=game.start, now=now)
                else None
            ),
            club_name=names.get(game.club_id),
            distance_km=distances.get(game.club_id),
            people=await people_on([game], self._people),
            leaving=leave_terms(
                game,
                state.status,
                card_fee_grosze=self._fees.card_fee_on(game.share_grosze),
                now=now,
            ),
        )
