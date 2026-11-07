"""A booked game's details, for a player in it (#542; the mechanics §14.2;
the screens A4.1) — and for a member the open seat on it is offered to (#545;
the screens A4.3).

**The card and the court facts, folded once.** Who is on which side, read from
the reader's own side; the status and the money line, as Home folds them, against
the same single instant; WHERE — the club, the court the booking was given, and
how far the club is from the reader's Location area — and the hour.

**The forecast is the game's pairing, read where it has always been read**
(``GET /games/{game_id}/pairing``, ``docs/adr/0161``): a booked game is an
ordinary Game, and its balance forecast is the card today's game screen draws
(the screens A4.1: *as built today*). What this read decides is **whether** it is
drawn — while the full game awaits its entry; never while a seat is open.

**No code to show at the desk**: desk check-in is removed (#651).

**What leaving would cost, before the reader leaves** (#544, #637, #641; the
mechanics §13): nothing before the cut-off — the hold is let go, so there is no
quote — after it, the share less **exactly the fee kept on the reader's own
payment** when somebody takes the seat, asked of the payments once a read and
**never an estimate**: no figure while that fee is not yet known; nothing paid
while a payment is awaited — and no button once the hour has come.

**The chat is a join, not a field** (``docs/adr/0149`` §3): the reader's rooms,
``GET /conversations``, carry the booked game's room by its ``game_id``.

**A rescue seen from outside** (#545): a member the open seat is offered to —
a Seat open card, a Seats to fill row — reads the booked layout with themself
in the seat that opened first (*You?*, unpaid), the court, the players *paid*,
and ``rescue``: when the seat leaves the board, and so what *I'm in* costs.
No *Leave*, and nothing that needs it.

**A game waiting for one payment** (#625) is read as Home reads it — off its
proposal, since it has no booking — with the time to pay, and *Leave*, which
withdraws the yes; **gone back to filling** (Q106), *Seat open*, nobody paid,
no court, and no *Leave* of its own — its way out is a game still filling's,
*Withdraw*.

**A friends game's invitee reads it from outside too** (#751): a friend its
seat is held for — waiting, or once they answered — sees the court with every
seat the card drew, their own among them, its share and its pay mode, and
nothing to leave.

**Refused with one code** — ``booking_not_found`` — for a booking that does not
exist and one the reader has no seat on and is not offered, so a booking id
says nothing about whose evening it is.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import final
from uuid import UUID

from app.kernel import Clock, Instant, Sport, instant
from app.modules.proposals.application.booked_people import people_on
from app.modules.proposals.application.friends import with_the_readers_friends
from app.modules.friends.domain.relation import FriendRelation
from app.modules.proposals.application.home import the_game
from app.modules.proposals.application.rescues import RescueOffers
from app.modules.proposals.domain.deck import Sides
from app.modules.proposals.domain.errors import BookingNotFound
from app.modules.proposals.domain.home import (
    BookedGame,
    BookedMoney,
    BookedState,
    LeaveTerms,
    Leaving,
    leave_terms,
    leaving_of,
    shows_forecast,
    state_of,
)
from app.modules.proposals.domain.rescues import (
    fills_by_the_cut_off,
    rescue_deadline,
    sides_for,
)
from app.modules.proposals.domain.ports import (
    HoldingTimes,
    ClubDistances,
    ClubNames,
    DeckPeople,
    ReaderRelations,
    DeckPerson,
    GameResults,
    LateRefunds,
    PlayerBookings,
    ProposalRepository,
)


@final
@dataclass(frozen=True, slots=True)
class RescueOffer:
    """The open seat, as offered to a reader who is not on the game (#545)."""

    #: When it leaves the board: the cut-off, then the start.
    deadline: Instant
    #: *fills by* the cut-off, or *offered until the start*.
    fills_by_the_cut_off: bool


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
    club_name: str | None
    #: ``None`` for a reader with no Location area.
    distance_km: float | None
    people: Mapping[tuple[Sport, UUID], DeckPerson]
    #: **The reader's** relation to everybody else on the game — the result's
    #: *PLAYED WITH* card and its pills (``docs/adr/0202`` §1). Empty for a
    #: reader not on the game.
    played_with: Mapping[UUID, FriendRelation] = field(default_factory=dict)
    #: What *Leave the game* would cost now — ``None`` where there is no button.
    leaving: LeaveTerms | None = None
    #: The open seat offered to a reader not on the game — ``None`` for a
    #: player in it (#545).
    rescue: RescueOffer | None = None


@final
class ReadBookingDetails:
    def __init__(
        self,
        *,
        bookings: PlayerBookings,
        proposals: ProposalRepository,
        results: GameResults,
        people: DeckPeople,
        clubs: ClubNames,
        distances: ClubDistances,
        late_refunds: LateRefunds,
        offers: RescueOffers,
        holding_times: HoldingTimes,
        relations: ReaderRelations,
        clock: Clock,
    ) -> None:
        self._relations = relations
        self._offers = offers
        self._holding_times = holding_times
        self._bookings = bookings
        self._proposals = proposals
        self._results = results
        self._people = people
        self._clubs = clubs
        self._distances = distances
        self._late_refunds = late_refunds
        self._clock = clock

    async def execute(self, booking_id: UUID, reader: UUID) -> BookingDetails:
        now = instant(self._clock.now())
        game = await the_game(
            booking_id, bookings=self._bookings, proposals=self._proposals, now=now
        )
        if game is None:
            raise BookingNotFound()
        if not game.has_a_seat_for(reader):
            if game.invitation_of(reader) is not None:
                return await self._as_invited(game, reader, now=now)
            if not await self._offers.is_offered(game, reader, now=now):
                raise BookingNotFound()
            return await self._from_outside(game, reader, now=now)
        result = (
            None
            if game.game_id is None
            else (await self._results.of([game.game_id], reader=reader, now=now)).get(
                game.game_id
            )
        )
        late_refund = (
            await self._late_refunds.of(game.booking_id, reader)
            if leaving_of(game, now=now) is Leaving.AFTER_THE_CUT_OFF
            else None
        )
        # The reader's own share, if it was only checked at the fill (#639).
        held_from = await self._holding_times.of(reader, [game.booking_id])
        state = state_of(
            game, result, now=now, held_from=held_from.get(game.booking_id)
        )
        names = await self._clubs.names_of([game.club_id])
        distances = await self._distances.from_player(reader, [game.club_id])
        return BookingDetails(
            game=game,
            read_at=now,
            state=state,
            sides=game.seen_by(reader),
            shows_forecast=shows_forecast(state.status),
            club_name=names.get(game.club_id),
            distance_km=distances.get(game.club_id),
            people=await with_the_readers_friends(
                await people_on([game], self._people),
                reader=reader,
                relations=self._relations,
            ),
            played_with=await self._relations.relations_of(
                reader, [player for player in game.players if player != reader]
            ),
            # Leaving a friends game is #752's: no *Leave* until then.
            leaving=None
            if game.is_friends_game
            else leave_terms(game, state.status, late_refund=late_refund, now=now),
        )

    async def _as_invited(
        self, game: BookedGame, reader: UUID, *, now: Instant
    ) -> BookingDetails:
        """A friends game as a friend invited to it sees it (#751): every seat
        the card drew, theirs among them, unpaid, and nothing to leave."""

        state = state_of(game, None, now=now)
        names = await self._clubs.names_of([game.club_id])
        distances = await self._distances.from_player(reader, [game.club_id])
        return BookingDetails(
            game=game,
            read_at=now,
            state=BookedState(
                status=state.status,
                needs_you=False,
                money=BookedMoney(
                    share_grosze=game.share_grosze,
                    paid=False,
                    free_to_leave_until=None,
                ),
                called_off=state.called_off,
                uncounted=state.uncounted,
            ),
            sides=game.seen_by(reader),
            shows_forecast=False,
            club_name=names.get(game.club_id),
            distance_km=distances.get(game.club_id),
            people=await with_the_readers_friends(
                await people_on([game], self._people),
                reader=reader,
                relations=self._relations,
            ),
        )

    async def _from_outside(
        self, game: BookedGame, reader: UUID, *, now: Instant
    ) -> BookingDetails:
        """The rescue as a member it is offered to sees it: in the seat that
        opened first, and nothing to leave."""

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
        people = await people_on([game], self._people)
        people.update(
            {
                (game.sport, player): person
                for player, person in (
                    await self._people.people([reader], sport=game.sport)
                ).items()
            }
        )
        return BookingDetails(
            game=game,
            read_at=now,
            state=BookedState(
                status=state.status,
                needs_you=False,
                # The reader has paid nothing, and has nothing to leave: their
                # line is *I'm in · 27 zł*.
                money=BookedMoney(
                    share_grosze=game.share_grosze,
                    paid=False,
                    free_to_leave_until=None,
                ),
                called_off=state.called_off,
                uncounted=state.uncounted,
            ),
            sides=sides_for(game, reader),
            shows_forecast=False,
            club_name=names.get(game.club_id),
            distance_km=distances.get(game.club_id),
            people=await with_the_readers_friends(
                people, reader=reader, relations=self._relations
            ),
            rescue=RescueOffer(
                deadline=rescue_deadline(game, now=now),
                fills_by_the_cut_off=fills_by_the_cut_off(game, now=now),
            ),
        )
