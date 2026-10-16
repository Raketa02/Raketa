"""**The last yes books the game** (the mechanics §11, §12.2; ``docs/adr/0189``
§2, §4–§5; #541).

The moment a yes leaves a game with no seat open, this is what happens to it, in
the yes's own transaction:

1. **The people.** The game fills the moment enough people who said yes **all
   fit each other** (§7) — and a pair already In can stop fitting after both
   said yes: one blocked the other. A yes is refused when it does not fit the
   people In (``guards.py``), so such a pair is two earlier yeses, and the later
   of them stops counting — their **seat reopens** (``NO_LONGER_FITS``) — and
   nobody is asked for money.
2. **The club.** A club that no longer sells, or has no court of the sport
   left at the hour, has taken the card's court hour: the card is over, nobody
   paid, and a payment a player had confirmed for it is let go. **No club is
   asked** (``docs/adr/0196`` §1): the game books at every club the moment it
   fills (#669).
3. **The money, all or nothing.** Every seat's share is held on the club's
   account; only when every one is held is any taken. When one is not, nobody
   pays, and **that player is given time to pay** (#625; Q109): thirty
   minutes, never past the book-by, their seat held for them alone and every
   other hold kept, so the payment in time books the game at once. **Before
   the club's cut-off it is time to fix the card** (#638; Q113): nothing is
   taken then, only held, so nothing is paid in it, and it is never past the
   cut-off either. With no time left — the book-by has come — the seats
   reopen.
4. **The booking.** The sides are drawn for the most even game — the engine's
   own forecast over every way the four could stand, as a card's are — and the
   Booking opens on the first free court, opening the Game and its chat. Two
   cards at one hour filling at once can both read the same court free: the
   second meets ``CourtJustTaken`` and the yes is tried once more
   (``answers.py``), its holds answered again under the same keys.
5. **What it does to everybody's other yeses.** Every other yes of the players
   at that hour is withdrawn — *one game per hour* — and a player whose games
   per week this booking reaches has their other yeses that week paused.

**Nothing here commits, and nothing here saves the proposal it was handed**: the
yes that filled it is the caller's, and so is the transaction — the money's
verdict, the booking, the game and every withdrawn yes stand or fall together.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from dataclasses import dataclass, field
from typing import final
from uuid import UUID

from app.kernel import Instant, invariant
from app.modules.proposals.application.members import genders_on
from app.modules.proposals.domain.deck import (
    arrangements,
    evenest,
    hour_taken,
    standing_for,
    week_of,
    week_window,
)
from app.modules.proposals.domain.ports import (
    BalanceForecasts,
    BookableCourt,
    BookedGames,
    ClubTerms,
    FullGame,
    GameBookings,
    GamesAndMoneyRepository,
    GameToCharge,
    PlayerFit,
    PlayersInPlay,
    ProposalDirectory,
    ProposalRepository,
    RefusedPayment,
    SeatCharges,
    UndecidedCharges,
)
from app.modules.proposals.application.time_to_pay import let_go_of_what_was_kept
from app.modules.proposals.domain.proposal import (
    Proposal,
    ReopenReason,
    Standing,
    TimeTo,
)


@final
@dataclass(frozen=True, slots=True)
class Booked:
    """The game booked: its booking — the proposal's own id — and its Game."""

    booking_id: UUID
    game_id: UUID


@final
@dataclass(frozen=True, slots=True)
class FillOutcome:
    """What the fill did. At most one of the four is set."""

    booked: Booked | None = None
    #: Whose share could not be held — nobody paid.
    refused: Mapping[UUID, RefusedPayment] = field(default_factory=dict)
    #: No court was left: the card is over.
    court_lost: bool = False
    #: The later yes of a pair In that stopped fitting each other: its seat
    #: reopened, and nothing was booked.
    no_longer_fit: frozenset[UUID] = frozenset()
    #: A refused share's time to pay (#625): the game waits for that payment
    #: until then, nobody paid. Set with ``refused``.
    paying_until: Instant | None = None
    #: What that time is for — to fix the card, or to pay (#638). Set with
    #: ``paying_until``.
    time_to: TimeTo | None = None


@final
class Fill:
    def __init__(
        self,
        *,
        proposals: ProposalRepository,
        directory: ProposalDirectory,
        terms: ClubTerms,
        bookings: GameBookings,
        charges: SeatCharges,
        undecided: UndecidedCharges,
        forecasts: BalanceForecasts,
        games_and_money: GamesAndMoneyRepository,
        booked: BookedGames,
        fit: PlayerFit,
        players: PlayersInPlay,
    ) -> None:
        self._fit = fit
        self._players = players
        self._proposals = proposals
        self._directory = directory
        self._terms = terms
        self._bookings = bookings
        self._charges = charges
        self._undecided = undecided
        self._forecasts = forecasts
        self._games_and_money = games_and_money
        self._booked = booked

    async def run(
        self, proposal: Proposal, *, by: UUID | None, now: Instant
    ) -> FillOutcome:
        """``by`` is the player whose own act left no seat open — their yes, a
        join, a confirmed payment — or ``None`` when no player's act did: a
        paused yes coming back. A game booked now records it
        (``ProposalFilled.filled_by``), so what it booked is never told back
        to them as news (the mechanics Q102)."""

        invariant(proposal.open_seats == 0, f"{proposal.proposal_id} is not full")
        if any(payer != by for payer in proposal.paying):
            # Full again while somebody's payment is still awaited — a seat
            # that opened in the wait was taken: it waits for that payment, and
            # only the payer's own act fills it. Nothing retries a card by
            # itself (Q109).
            return FillOutcome(paying_until=proposal.pay_by, time_to=proposal.time_to)
        unfit = await self._no_longer_fit(proposal, now=now)
        if unfit:
            return FillOutcome(no_longer_fit=unfit)
        terms = (await self._terms.of([proposal.club_id], now=now)).get(
            proposal.club_id
        )
        court = (
            None
            if terms is None
            else await self._bookings.court_for(
                proposal.club_id, sport=proposal.sport, start=proposal.start
            )
        )
        if terms is None or court is None:
            proposal.lose_court_hour(at=now)
            await self._undecided.release(proposal.proposal_id, keeping=(), at=now)
            return FillOutcome(court_lost=True)
        return await self._paid_and_booked(proposal, court, by=by, now=now)

    async def _paid_and_booked(
        self,
        proposal: Proposal,
        court: BookableCourt,
        *,
        by: UUID | None,
        now: Instant,
    ) -> FillOutcome:
        """Every seat's share, all or nothing; then the booking on ``court``,
        with the sides drawn for the most even game — and what it does to
        everybody's other yeses. A refused share is given its time to pay,
        every other hold kept for it (#625)."""

        players = proposal.yeses
        cut_off = court.cut_off
        # A share refused now has until then — ``None`` once the book-by has
        # come; a payer refused again keeps the time they had. Before the
        # cut-off it is time to fix the card, and never past it (#638).
        pay_by = proposal.time_to_pay_ends(now, cut_off=cut_off)
        charged = await self._charges.charge(
            GameToCharge(
                proposal_id=proposal.proposal_id,
                club_id=proposal.club_id,
                sport=proposal.sport,
                start=proposal.start,
                share_grosze=proposal.share_grosze,
                court_name=court.name,
                free_to_leave_until=cut_off if now < cut_off else None,
                pay_by=pay_by,
                paying_until=proposal.payments_due,
                # Told *It's a game!* when it filled: *booked · you paid* now
                # (Q110).
                booked_on_a_payment=bool(proposal.paying),
                filled_by=by,
            ),
            players,
            # The game's own record of its tries, so a retried request asks for
            # the same holds and the next try after a refusal asks afresh.
            attempt=proposal.version,
            at=now,
        )
        if charged.refused:
            return await self._refused(
                proposal,
                charged.refused,
                pay_by=pay_by,
                time_to=TimeTo.at(now, cut_off=cut_off),
                by=by,
                now=now,
            )

        first_side, second_side = await self._sides(proposal)
        proposal.fill(first_side=first_side, second_side=second_side, by=by, at=now)
        game_id = await self._bookings.book(
            FullGame(
                proposal_id=proposal.proposal_id,
                pool_id=proposal.pool.id,
                club_id=proposal.club_id,
                sport=proposal.sport,
                kind=proposal.kind,
                start=proposal.start,
                share_grosze=proposal.share_grosze,
                first_side=first_side,
                second_side=second_side,
                court=court,
            ),
            at=now,
        )
        # A refused payment somebody since took the seat from, or a hold a
        # player confirmed and this game was paid without, is let go.
        await self._undecided.release(
            proposal.proposal_id, keeping=frozenset(charged.taken.values()), at=now
        )
        await self.other_yeses(
            proposal.yeses,
            booked_id=proposal.proposal_id,
            start=proposal.start,
            now=now,
        )
        return FillOutcome(
            booked=Booked(booking_id=proposal.proposal_id, game_id=game_id)
        )

    async def _refused(
        self,
        proposal: Proposal,
        refused: Mapping[UUID, RefusedPayment],
        *,
        pay_by: Instant | None,
        time_to: TimeTo,
        by: UUID | None,
        now: Instant,
    ) -> FillOutcome:
        """Nobody paid. **Each refused share's player has until ``pay_by``**,
        their seat held for them alone — to fix the card or to pay
        (``time_to``, #638). With no time left — the book-by has come — the
        seats reopen."""

        payers = tuple(sorted(refused, key=str))
        if pay_by is None:
            for player in payers:
                proposal.reopen_seat(
                    player,
                    reason=ReopenReason(refused[player].refusal.value),
                    seat_charge_id=refused[player].seat_charge_id,
                    at=now,
                )
            return FillOutcome(refused=refused)
        for player in payers:
            proposal.give_time_to_pay(
                player,
                reason=ReopenReason(refused[player].refusal.value),
                seat_charge_id=refused[player].seat_charge_id,
                until=pay_by,
                time_to=time_to,
                filled_by=by,
                at=now,
            )
        return FillOutcome(
            refused=refused, paying_until=proposal.pay_by, time_to=proposal.time_to
        )

    async def _no_longer_fit(
        self, proposal: Proposal, *, now: Instant
    ) -> frozenset[UUID]:
        """The later yes of every pair In that no longer fits — each seat
        reopened. **Never for the reliability filter**: every yes here was
        given already, and the filter takes none back (``docs/adr/0195`` §6)."""

        unfit = await self._fit.unfit_pairs(
            proposal.yeses,
            sport=proposal.sport,
            kind=proposal.kind,
            at=now,
            reliability_filter=False,
        )
        if not unfit:
            return frozenset()
        said = {player: order for order, player in enumerate(proposal.yeses)}
        later = frozenset(max(pair, key=said.__getitem__) for pair in unfit)
        for player in proposal.yeses:
            if player in later:
                proposal.reopen_seat(
                    player,
                    reason=ReopenReason.NO_LONGER_FITS,
                    seat_charge_id=None,
                    at=now,
                )
        return later

    async def _sides(
        self, proposal: Proposal
    ) -> tuple[tuple[UUID, ...], tuple[UUID, ...]]:
        """The most even way the people In could stand — the engine's forecast
        over every arrangement, the first among equals — as a card draws its
        sides (``domain/deck.py``): on a *Mixed pairs* post, a man and a woman
        a side (#546)."""

        first, *others = proposal.yeses
        options = standing_for(
            arrangements(first, others, seats_per_side=proposal.seats_per_side),
            who=proposal.who,
            genders=await genders_on(self._players, proposal, proposal.yeses),
        )
        sides, _ = evenest(
            options, await self._forecasts.forecasts(options, sport=proposal.sport)
        )
        return tuple(sides.yours), tuple(sides.theirs)

    async def other_yeses(
        self,
        players: Collection[UUID],
        *,
        booked_id: UUID,
        start: Instant,
        now: Instant,
    ) -> None:
        """Every other yes of these players at the booked hour is withdrawn,
        and a player whose week this booking fills has their other yeses that
        week paused (the mechanics §6.6, §11.5) — the fill's, and a rescue's
        for the one who took the seat (#545). **After the booking is saved**,
        so the week's count already holds it."""

        week = week_of(start)
        window_start, window_end = week_window([week])
        loaded: dict[UUID, Proposal] = {}
        for player in players:
            settings = await self._games_and_money.load(player)
            # The booking was saved before this, and its row flushed: the
            # count already holds it.
            capped = (
                len(
                    await self._booked.starts_of(
                        player, start=window_start, end=window_end
                    )
                )
                >= settings.games_per_week
            )
            for yes in await self._directory.live_yeses_of(player, now=now):
                if yes.proposal_id == booked_id:
                    continue
                same_hour = hour_taken(yes.start, [start])
                if not same_hour and not (capped and week_of(yes.start) == week):
                    continue
                other = loaded.get(yes.proposal_id) or await self._proposals.load(
                    yes.proposal_id
                )
                if other is None or other.standing_at(now) is not Standing.FILLING:
                    continue
                loaded[yes.proposal_id] = other
                was_paying = dict(other.paying)
                if same_hour:
                    # Not their own act: nobody is told whose hour it was.
                    other.withdraw_yes(player, at=now, own=False)
                else:
                    other.pause_yes(player, at=now)
                await self._proposals.save(other)
                await let_go_of_what_was_kept(
                    other, was_paying, leaver=player, undecided=self._undecided, at=now
                )
