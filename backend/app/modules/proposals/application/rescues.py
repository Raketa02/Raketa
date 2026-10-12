"""**Rescues: seats to fill** (#545; the mechanics §8.1, §10.1, §12.3, §19; the
screens A2.3, A3.1, A4.3).

A booked game that lost a player offers the seat. Three things here:

- **who it is offered to** (``RescueOffers``) — read live, once per provider
  over everybody asked about: each member's Play intent, week, booked games and
  Games & money, and the pair rule over them and the people on the games; the
  rules are ``domain/rescues.py``'s. The board offers it to every member who
  fits and is free; the deck deals it to the best fits;
- **taking it** (``Rescuer``, ``JoinARescue``) — the client gave its ten
  seconds of *Undo* first. **The game is locked first** — its proposal's row,
  the booking's own id — as every act on a game is, so two players going for
  the last seat are one after the other: **the first wins**, and the second
  reads it gone (``seat_just_taken``) before anybody asks their bank. Then the
  joiner's share is **held until the cut-off, like the seats it joins** — or
  checked, and held at its Holding time, far ahead of it — **or taken at once
  after it** (#637, #639, #640): the fill's own all-or-nothing, for one seat
  (``SeatCharges``, ``rescue``), and the answer says which (``money``). The
  seat that opened first is theirs on the booking and on its Game, and **the
  leaver who left after the cut-off is refunded, less exactly the fee kept on
  their payment, the moment the joiner's payment succeeds** (#641): the refund
  is decided here, in the same transaction, and made — and told, to the grosz
  — from the outbox, waiting for a fee not yet known. **A refused payment
  keeps a seat for the joiner alone** (#640) — thirty minutes to fix the card
  before the cut-off, or to pay after it, never past the start — offered to
  nobody else meanwhile, and **confirming it is the join again**
  (``POST /seat-charges/{id}/confirmation``); run out, it is offered again,
  theirs to take while it is free, and never kept for them again. The
  joiner's other yeses at the hour are withdrawn and a full week pauses the
  rest, as a fill does;
- **a no to it** (``SayNoToARescue``) — the Seat open card leaves that reader's
  deck for good. The board still lists the seat: it is every rescue they fit.

**Nothing is told to anybody here**: *Fill in alerts* and *You've been
refunded* as a push are #549's; the leaver's refund is emailed, as every notice
about money is.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from typing import final
from uuid import UUID

from app.application.ports import UnitOfWork
from app.engines.matchfit.core import SearchMode
from app.kernel import Clock, Instant, Sport, instant, invariant
from app.modules.proposals.application.answers import YesAnswer
from app.modules.proposals.application.commands import (
    ReadFillInCommand,
    RescueCommand,
)
from app.modules.proposals.application.fill import Booked, Fill
from app.modules.proposals.application.guards import Guards
from app.modules.proposals.domain.deck import (
    CardForecast,
    Sides,
    week_of,
    week_window,
    weeks_ahead,
)
from app.modules.proposals.domain.errors import (
    BookingIsCalledOff,
    BookingNotFound,
    GameHasStarted,
    PaymentMethodRequired,
    PaymentToConfirm,
    PoolNotFound,
    RescueNotOffered,
    SeatJustTaken,
)
from app.modules.proposals.domain.home import BookedGame, BookedMoney, money_of
from app.modules.proposals.domain.ports import (
    BalanceForecasts,
    BookedGameChanges,
    BookedGames,
    ClubNames,
    DeckPeople,
    DeckPerson,
    GamesAndMoneyRepository,
    GameToCharge,
    HoldingTimes,
    PlayerBookings,
    PlayerFit,
    PlayersInPlay,
    Pools,
    ProposalRepository,
    RefundReason,
    SavedMethods,
    SeatCharges,
    SeatRefunds,
    UndecidedCharges,
    WantedKinds,
)
from app.modules.proposals.domain.pool import Pool
from app.modules.proposals.domain.proposal import Proposal, TimeTo
from app.modules.proposals.domain.rescues import (
    Candidate,
    best_fits,
    fills_by_the_cut_off,
    kept_until,
    offered_to,
    rescue_deadline,
    rescuable,
    sides_for,
)

# --------------------------------------------------------------------------- #
# Who a seat is offered to
# --------------------------------------------------------------------------- #


@final
@dataclass(frozen=True, slots=True)
class BestFits:
    """The members a rescue's card is dealt to, and the forecast of each one's
    game with them in the seat."""

    players: frozenset[UUID]
    forecasts: Mapping[UUID, CardForecast | None]


@final
@dataclass(frozen=True, slots=True)
class DealtRescue:
    """A rescue dealt to the reader as a Seat open card: the game, the sides
    they would stand in, and its forecast."""

    game: BookedGame
    sides: Sides
    forecast: CardForecast | None


@final
class RescueOffers:
    """**Read live, every read**: the pair rule and the forecasts are one read
    per kind over everybody asked about, and each member's intent, week, booked
    games and Games & money are read per member, as the proposer reads them —
    so the whole pool is read only when a seat is offered to the reader."""

    def __init__(
        self,
        *,
        pools: Pools,
        bookings: PlayerBookings,
        wanted: WantedKinds,
        settings: GamesAndMoneyRepository,
        booked: BookedGames,
        players: PlayersInPlay,
        fit: PlayerFit,
        forecasts: BalanceForecasts,
    ) -> None:
        self._pools = pools
        self._bookings = bookings
        self._wanted = wanted
        self._settings = settings
        self._booked = booked
        self._players = players
        self._fit = fit
        self._forecasts = forecasts

    async def in_pool(
        self, pool_id: UUID, *, sport: Sport, now: Instant
    ) -> list[BookedGame]:
        """The pool's rescues in the sport with a seat open now, soonest first
        — a seat kept for a refused rescuer too (#640), which only they are
        offered."""

        return [
            game
            for game in await self._bookings.rescues_in(pool_id, sport=sport, now=now)
            if rescuable(game, now=now)
        ]

    async def candidates(
        self,
        players: Sequence[UUID],
        *,
        sport: Sport,
        games: Sequence[BookedGame],
        now: Instant,
    ) -> dict[UUID, Candidate]:
        """What the offer reads of each of these players, around these games'
        weeks."""

        if not players or not games:
            return {}
        start, end = week_window(_weeks_of(games, now=now))
        in_play = await self._players.of(players, sport=sport)
        found: dict[UUID, Candidate] = {}
        for player in players:
            wanted = await self._wanted.of(player, sport=sport)
            found[player] = Candidate(
                player_id=player,
                wants=wanted or frozenset(),
                week=in_play[player].week,
                booked=tuple(
                    await self._booked.starts_of(player, start=start, end=end)
                ),
                limits=await self._settings.load(player),
            )
        return found

    async def offered(
        self,
        games: Sequence[BookedGame],
        candidates: Mapping[UUID, Candidate],
        *,
        sport: Sport,
        now: Instant,
    ) -> dict[UUID, tuple[UUID, ...]]:
        """Each game's members it is offered to, in ``candidates``' order —
        one pair rule read per kind over everybody, never one per game."""

        unfit: dict[SearchMode, frozenset[frozenset[UUID]]] = {}
        # In the enum's order rather than a set's, so the reads run alike on
        # every process (docs/adr/0105).
        for kind in [kind for kind in SearchMode if any(g.kind is kind for g in games)]:
            everybody = {
                *candidates,
                *(
                    player
                    for game in games
                    if game.kind is kind
                    for player in game.players
                ),
            }
            unfit[kind] = await self._fit.unfit_pairs(
                sorted(everybody, key=str), sport=sport, kind=kind, at=now
            )
        return {
            game.booking_id: tuple(
                player
                for player, candidate in candidates.items()
                if offered_to(game, candidate, unfit=unfit[game.kind], now=now)
            )
            for game in games
        }

    async def best_fits(
        self, game: BookedGame, offered: Sequence[UUID], *, sport: Sport
    ) -> BestFits:
        """Of the members offered, the ones the deck deals the seat to."""

        options = [sides_for(game, player) for player in offered]
        forecasts = (
            await self._forecasts.forecasts(options, sport=sport) if options else []
        )
        return BestFits(
            players=best_fits(game, offered, forecasts),
            forecasts=dict(zip(offered, forecasts, strict=True)),
        )

    async def offered_to_one(
        self,
        games: Sequence[BookedGame],
        player: UUID,
        *,
        sport: Sport,
        now: Instant,
    ) -> list[BookedGame]:
        """Those of these games whose seat is offered to this one player."""

        candidates = await self.candidates([player], sport=sport, games=games, now=now)
        offered = await self.offered(games, candidates, sport=sport, now=now)
        return [game for game in games if player in offered[game.booking_id]]

    async def is_offered(self, game: BookedGame, player: UUID, *, now: Instant) -> bool:
        """Whether this rescue is offered to this one player now — a member of
        its pool, as the board and the deck read only their own pool's."""

        if not rescuable(game, now=now, by=player):
            return False
        pool = await self._pools.find(game.pool_id)
        if pool is None or not await self._pools.members_among(pool, [player]):
            return False
        return bool(
            await self.offered_to_one([game], player, sport=game.sport, now=now)
        )

    async def dealt_to(
        self,
        pool: Pool,
        reader: UUID,
        *,
        sport: Sport,
        kinds: Collection[SearchMode],
        now: Instant,
    ) -> list[DealtRescue]:
        """The pool's rescues of these kinds dealt to the reader as Seat open
        cards: offered to them, not said no to, and **they are one of its best
        fits**. **The reader is asked about first**: the whole pool is read only
        when a seat is offered to them at all."""

        games = [
            game
            for game in await self.in_pool(pool.id, sport=sport, now=now)
            if game.kind in kinds and reader not in game.said_no
        ]
        games = await self.offered_to_one(games, reader, sport=sport, now=now)
        if not games:
            return []
        everybody = await self.candidates(
            await self._pools.members_of(pool), sport=sport, games=games, now=now
        )
        offered = await self.offered(games, everybody, sport=sport, now=now)
        dealt: list[DealtRescue] = []
        for game in games:
            # A no is the seat dealt to the next best fit (the mechanics §6.2):
            # whoever said one holds no place among them.
            fits = await self.best_fits(
                game,
                [p for p in offered[game.booking_id] if p not in game.said_no],
                sport=sport,
            )
            if reader in fits.players:
                dealt.append(
                    DealtRescue(
                        game=game,
                        sides=sides_for(game, reader),
                        forecast=fits.forecasts.get(reader),
                    )
                )
        return dealt


def _weeks_of(games: Sequence[BookedGame], *, now: Instant) -> tuple[date, ...]:
    """Every week from now's to the latest game's — each game's week counted
    against its player's games per week."""

    ahead = weeks_ahead(now)
    last = max([ahead[-1], *(week_of(game.start) for game in games)])
    weeks = list(ahead)
    while weeks[-1] < last:
        weeks.append(date.fromordinal(weeks[-1].toordinal() + 7))
    return tuple(weeks)


# --------------------------------------------------------------------------- #
# Taking a seat
# --------------------------------------------------------------------------- #


@final
class Rescuer:
    """The join itself, inside its caller's transaction and lock — *I'm in* on
    a rescue, and a refused rescue payment confirmed. **No commit.**"""

    def __init__(
        self,
        *,
        bookings: PlayerBookings,
        offers: RescueOffers,
        guards: Guards,
        methods: SavedMethods,
        changes: BookedGameChanges,
        charges: SeatCharges,
        refunds: SeatRefunds,
        undecided: UndecidedCharges,
        holding_times: HoldingTimes,
        fill: Fill,
    ) -> None:
        self._bookings = bookings
        self._offers = offers
        self._guards = guards
        self._methods = methods
        self._changes = changes
        self._charges = charges
        self._refunds = refunds
        self._undecided = undecided
        self._holding_times = holding_times
        self._fill = fill

    async def join(
        self,
        proposal: Proposal | None,
        booking_id: UUID,
        player: UUID,
        *,
        now: Instant,
        confirmed: UUID | None = None,
    ) -> YesAnswer:
        """Take the seat that opened first, or refuse — ``confirmed`` is the
        refused payment the player has just confirmed, which the join takes
        rather than asking the bank again. A refused payment keeps a seat for
        them (#640)."""

        game = await self._bookings.find(booking_id)
        if (
            proposal is None
            or game is None
            or not await self._guards.in_the_pool(proposal.pool, [player])
        ):
            # A stranger learns nothing about a group's games.
            raise BookingNotFound()
        if game.has_a_seat_for(player):
            # Taken already — a second tap, or the request retried. A payment
            # confirmed for it since is not the one they paid with: let go.
            if confirmed is not None:
                await self._undecided.release(
                    booking_id, keeping=(), of_player=player, at=now
                )
            return await self._joined(game, player, open_seats=game.open_seats, now=now)
        if game.called_off_reason(now) is not None:
            raise BookingIsCalledOff()
        if now >= game.start:
            raise GameHasStarted()
        if game.keep_to_run_out(player, now=now):
            # Their own act come too late runs their time out first, as the
            # job would have: the seat is offered to anybody now, them too.
            await self._changes.kept_seat_ran_out(booking_id, player, at=now)
            game = invariant(
                await self._bookings.find(booking_id),
                f"{booking_id} gone in its own transaction",
            )
        if not rescuable(game, now=now, by=player):
            raise SeatJustTaken()
        if not await self._offers.is_offered(game, player, now=now):
            raise RescueNotOffered()
        waiting = await self._charges.to_confirm(booking_id, player_id=player)
        if waiting is not None and waiting != confirmed:
            # Their earlier try waits on their bank: asking again off the same
            # card meets the same answer. Confirming it is the join again.
            raise PaymentToConfirm(seat_charge_id=str(waiting))
        if confirmed is None and not await self._methods.saved_for(player):
            # A confirmed payment is held already: it needs no method to take.
            raise PaymentMethodRequired()

        # Refused, a seat is kept for them — once (#640).
        until = kept_until(game, player, now=now)
        kept = game.kept_for(player, now=now)
        charged = await self._charges.charge(
            GameToCharge(
                proposal_id=booking_id,
                club_id=game.club_id,
                sport=game.sport,
                start=game.start,
                share_grosze=game.share_grosze,
                court_name=game.court_name,
                free_to_leave_until=(
                    game.cut_off if fills_by_the_cut_off(game, now=now) else None
                ),
                rescue=True,
                pay_by=until,
                paying_until={} if kept is None else {player: kept.until},
            ),
            [player],
            # The booking's own record of its tries: a retried request is
            # answered the same hold, and a seat that opened since — or kept
            # since — asks afresh.
            attempt=game.version,
            at=now,
        )
        refused = charged.refused.get(player)
        if refused is not None:
            time_to = TimeTo.at(now, cut_off=game.cut_off)
            if until is not None:
                await self._changes.keep_the_seat(
                    booking_id,
                    player,
                    until=until,
                    refused=refused,
                    time_to=time_to,
                    at=now,
                )
            return YesAnswer(
                proposal_id=booking_id,
                open_seats=game.open_seats,
                your_payment=refused,
                kept_until=until,
                time_to=None if until is None else time_to,
            )

        taken = await self._changes.rescue(booking_id, player, at=now)
        if taken.left_at >= game.cut_off:
            # Left after the cut-off: refunded only now somebody took the seat.
            await self._refunds.refund(
                booking_id, [taken.left_by], reason=RefundReason.SEAT_TAKEN, at=now
            )
        still_open = game.open_seats - 1
        if still_open == 0:
            # The board is gone: a payment somebody else confirmed for a seat
            # here is let go, and nobody pays it.
            await self._undecided.release(
                booking_id, keeping=frozenset(charged.taken.values()), at=now
            )
        await self._fill.other_yeses(
            [player], booked_id=booking_id, start=game.start, now=now
        )
        return await self._joined(game, player, open_seats=still_open, now=now)

    async def _joined(
        self, game: BookedGame, player: UUID, *, open_seats: int, now: Instant
    ) -> YesAnswer:
        """The seat taken, and the joiner's money line as Home reads it (#640):
        held until the cut-off — or checked, and held from its Holding time —
        or taken, after it."""

        assert game.game_id is not None, f"a booked game {game.booking_id} with no Game"
        held_from = await self._holding_times.of(player, [game.booking_id])
        money: BookedMoney = money_of(
            game, now=now, held_from=held_from.get(game.booking_id)
        )
        return YesAnswer(
            proposal_id=game.booking_id,
            open_seats=open_seats,
            booked=Booked(booking_id=game.booking_id, game_id=game.game_id),
            money=money,
        )


@final
class JoinARescue:
    """*I'm in · 27 zł* on a Seat open card, a Seats to fill row, or a
    rescue's details."""

    def __init__(
        self,
        *,
        proposals: ProposalRepository,
        rescuer: Rescuer,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._proposals = proposals
        self._rescuer = rescuer
        self._uow = uow
        self._clock = clock

    async def execute(self, command: RescueCommand) -> YesAnswer:
        now = instant(self._clock.now())
        # The booking's id is its proposal's, whose row every act on the game
        # locks first.
        proposal = await self._proposals.load_for_update(command.booking_id)
        answer = await self._rescuer.join(
            proposal, command.booking_id, command.player_id, now=now
        )
        await self._uow.commit()
        return answer


@final
class SayNoToARescue:
    """*Not this time* on a Seat open card: silent, and never on the record."""

    def __init__(
        self,
        *,
        proposals: ProposalRepository,
        bookings: PlayerBookings,
        offers: RescueOffers,
        changes: BookedGameChanges,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._proposals = proposals
        self._bookings = bookings
        self._offers = offers
        self._changes = changes
        self._uow = uow
        self._clock = clock

    async def execute(self, command: RescueCommand) -> None:
        now = instant(self._clock.now())
        proposal = await self._proposals.load_for_update(command.booking_id)
        game = await self._bookings.find(command.booking_id)
        if (
            proposal is None
            or game is None
            or not await self._offers.is_offered(game, command.player_id, now=now)
        ):
            # Only a seat dealt to them is theirs to say no to; a card already
            # gone is the stranger's answer.
            raise BookingNotFound()
        await self._changes.say_no_to_the_seat(
            command.booking_id, command.player_id, at=now
        )
        await self._uow.commit()


# --------------------------------------------------------------------------- #
# The board
# --------------------------------------------------------------------------- #


@final
@dataclass(frozen=True, slots=True)
class SeatToFill:
    """One *Seats to fill* row: the booked game, and when its seat leaves the
    board — *fills by* the cut-off, then *offered until the start*."""

    game: BookedGame
    deadline: Instant
    fills_by_the_cut_off: bool
    club_name: str | None


@final
@dataclass(frozen=True, slots=True)
class FillIn:
    pool_id: UUID
    sport: Sport
    read_at: Instant
    #: Soonest first.
    seats_to_fill: tuple[SeatToFill, ...]
    #: Everybody on those games, as their small posters draw them.
    people: Mapping[UUID, DeckPerson]

    @property
    def badge(self) -> int:
        """The *Fill in* tab's badge: its Seats to fill rows."""

        return len(self.seats_to_fill)


@final
class ReadFillIn:
    """A group's *Fill in* tab for one reader and sport: **Seats to fill** —
    every rescue they fit and are free for, before or after the cut-off — and
    its badge. A read, recorded nowhere."""

    def __init__(
        self,
        *,
        pools: Pools,
        offers: RescueOffers,
        people: DeckPeople,
        clubs: ClubNames,
        clock: Clock,
    ) -> None:
        self._pools = pools
        self._offers = offers
        self._people = people
        self._clubs = clubs
        self._clock = clock

    async def execute(self, command: ReadFillInCommand) -> FillIn:
        now = instant(self._clock.now())
        reader, sport = command.player_id, command.sport
        pool = await self._pools.find(command.pool_id)
        # A stranger learns nothing about a group's games: one code for a pool
        # that does not exist and one they are not in.
        if pool is None or not await self._pools.members_among(pool, [reader]):
            raise PoolNotFound()
        rows = await self._offers.offered_to_one(
            await self._offers.in_pool(pool.id, sport=sport, now=now),
            reader,
            sport=sport,
            now=now,
        )
        names = await self._clubs.names_of({game.club_id for game in rows})
        return FillIn(
            pool_id=pool.id,
            sport=sport,
            read_at=now,
            seats_to_fill=tuple(
                SeatToFill(
                    game=game,
                    deadline=rescue_deadline(game, now=now),
                    fills_by_the_cut_off=fills_by_the_cut_off(game, now=now),
                    club_name=names.get(game.club_id),
                )
                for game in rows
            ),
            people=await self._people.people(
                sorted({player for game in rows for player in game.players}, key=str),
                sport=sport,
            ),
        )
