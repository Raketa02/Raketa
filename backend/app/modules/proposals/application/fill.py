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
   paid, and a payment a player had confirmed for it is let go. **An On request
   club is asked** (#543; the mechanics §16.8): the first free court is held
   for its answer, the sides are drawn, the desk is emailed, and nobody pays —
   the game waits, full, until the club says yes (``accept``, steps 3–5 then)
   or no.
3. **The money, all or nothing.** Every seat's share is held on the club's
   account; only when every one is held is any taken. When one is not, nobody
   pays, and **that player is given time to pay** (#625, #626; Q109): thirty
   minutes, never past the book-by, their seat held for them alone and every
   other hold kept, so the payment in time books the game at once — at the
   club's yes, without asking the club again. **Before the club's cut-off it
   is time to fix the card** (#638; Q113): nothing is taken then, only held,
   so nothing is paid in it, and it is never past the cut-off either. With no
   time left — the club said yes past the book-by — the game is called off at
   once.
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
The club's yes is the same: its transaction is the caller's.

**A seat opening on a game that waits for its club withdraws the request**:
whoever takes the yes away — the fill's own *one game per hour* and *games per
week* here, the player's *Leave*, a leaver of the group — tells the club it is
off (``ClubRequests.withdraw``), in the same transaction, so the held court is
free the moment the seat is.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Collection, Mapping
from dataclasses import dataclass, field
from typing import final
from uuid import UUID

from app.kernel import Instant, invariant, shifted
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
    ClubRequest,
    ClubRequests,
    ClubTerms,
    FullGame,
    GameBookings,
    GamesAndMoneyRepository,
    GameToAsk,
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
    """What the fill did. At most one of the five is set."""

    booked: Booked | None = None
    #: Put to its On request club, which has until then to answer — nobody
    #: paid.
    waiting_until: Instant | None = None
    #: Whose share could not be held — nobody paid.
    refused: Mapping[UUID, RefusedPayment] = field(default_factory=dict)
    #: No court was left: the card is over.
    court_lost: bool = False
    #: The later yes of a pair In that stopped fitting each other: its seat
    #: reopened, and nothing was booked.
    no_longer_fit: frozenset[UUID] = frozenset()
    #: A refused share's time to pay (#625, #626): the game waits for that
    #: payment until then, nobody paid. Set with ``refused``.
    paying_until: Instant | None = None
    #: What that time is for — to fix the card, or to pay (#638). Set with
    #: ``paying_until``.
    time_to: TimeTo | None = None
    #: The club said yes with no time left to pay — its book-by had come: the
    #: game is called off, nobody paid (#626). Set with ``refused``.
    called_off: bool = False


@final
class Fill:
    def __init__(
        self,
        *,
        proposals: ProposalRepository,
        directory: ProposalDirectory,
        terms: ClubTerms,
        bookings: GameBookings,
        requests: ClubRequests,
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
        self._requests = requests
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
        to them as news (the mechanics Q102); one put to its club is filled by
        the club's yes, which is nobody's — and its request records whose act
        put it there (``BookingRequested.filled_by``), so the *It's a game!*
        the four are told then is theirs already seen (#622)."""

        invariant(proposal.open_seats == 0, f"{proposal.proposal_id} is not full")
        if any(payer != by for payer in proposal.paying):
            # Full again while somebody's payment is still awaited — a seat
            # that opened in the wait was taken: it waits for that payment, and
            # only the payer's own act fills it. Nothing retries a card by
            # itself, and no club is asked while a payment is awaited (Q109).
            return FillOutcome(paying_until=proposal.pay_by, time_to=proposal.time_to)
        on_the_clubs_yes = proposal.on_the_clubs_yes
        unfit = await self._no_longer_fit(proposal, now=now)
        if unfit:
            if on_the_clubs_yes:
                # The request goes with the seat, and the club's yes with it.
                await self._withdraw_the_request(proposal, unfit, now=now)
            return FillOutcome(no_longer_fit=unfit)
        if on_the_clubs_yes:
            return await self._the_payment_the_club_waited_on(proposal, by=by, now=now)
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
        if terms.confirms_each_game:
            return await self._ask_the_club(proposal, court, by=by, now=now)
        return await self._paid_and_booked(
            proposal,
            court_name=court.name,
            cut_off=court.cut_off,
            sides=None,
            by=by,
            book=lambda first, second: self._bookings.book(
                FullGame(
                    proposal_id=proposal.proposal_id,
                    pool_id=proposal.pool.id,
                    club_id=proposal.club_id,
                    sport=proposal.sport,
                    kind=proposal.kind,
                    start=proposal.start,
                    share_grosze=proposal.share_grosze,
                    first_side=first,
                    second_side=second,
                    court=court,
                ),
                at=now,
            ),
            now=now,
        )

    async def accept(
        self, proposal: Proposal, request: ClubRequest, *, now: Instant
    ) -> FillOutcome:
        """**The club said yes** (the mechanics §16.8): everybody is charged
        now, all together or not at all, on the court held for the answer and
        with the sides the players have been reading — and the game is booked.
        A pair In that stopped fitting while it waited, or a share that cannot
        be held, opens a seat instead: nobody pays, the request is off, and the
        game is filling again."""

        invariant(
            proposal.waiting_for_the_club and request.waiting,
            f"{proposal.proposal_id} is accepted while not waiting for its club",
        )
        unfit = await self._no_longer_fit(proposal, now=now)
        if unfit:
            await self._withdraw_the_request(proposal, unfit, now=now)
            return FillOutcome(no_longer_fit=unfit)
        return await self._paid_and_booked(
            proposal,
            court_name=request.court_name,
            cut_off=request.cut_off,
            sides=(request.first_side, request.second_side),
            # The club's yes: no player's own act filled it.
            by=None,
            book=lambda first, second: self._requests.accept(
                proposal.proposal_id, at=now
            ),
            now=now,
            asked=True,
        )

    async def _the_payment_the_club_waited_on(
        self, proposal: Proposal, *, by: UUID | None, now: Instant
    ) -> FillOutcome:
        """**The club said yes, and the payment its yes waited on is in**
        (#626): booked on the held court, the club not asked again, with the
        sides the players were reading."""

        request = invariant(
            await self._requests.find(proposal.proposal_id),
            f"{proposal.proposal_id} waits on the club's yes with no request",
        )
        return await self._paid_and_booked(
            proposal,
            court_name=request.court_name,
            cut_off=request.cut_off,
            sides=(request.first_side, request.second_side),
            by=by,
            book=lambda first, second: self._requests.accept(
                proposal.proposal_id, at=now
            ),
            now=now,
            asked=True,
        )

    async def _ask_the_club(
        self,
        proposal: Proposal,
        court: BookableCourt,
        *,
        by: UUID | None,
        now: Instant,
    ) -> FillOutcome:
        """An On request club: the court is held for its answer and its desk is
        told; nobody pays until it says yes."""

        first_side, second_side = await self._sides(proposal)
        answer_by = shifted(now, court.time_to_confirm)
        await self._requests.ask(
            GameToAsk(
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
                answer_by=answer_by,
                filled_by=by,
            ),
            at=now,
        )
        return FillOutcome(waiting_until=answer_by)

    async def _paid_and_booked(
        self,
        proposal: Proposal,
        *,
        court_name: str,
        cut_off: Instant,
        sides: tuple[tuple[UUID, ...], tuple[UUID, ...]] | None,
        by: UUID | None,
        book: Callable[[tuple[UUID, ...], tuple[UUID, ...]], Awaitable[UUID]],
        now: Instant,
        asked: bool = False,
    ) -> FillOutcome:
        """Every seat's share, all or nothing; then the booking — ``book``,
        handed the sides — and what it does to everybody's other yeses. A
        refused share is given its time to pay, every other hold kept for it
        (#625, #626)."""

        players = proposal.yeses
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
                court_name=court_name,
                free_to_leave_until=cut_off if now < cut_off else None,
                pay_by=pay_by,
                paying_until=proposal.payments_due,
                # Told *It's a game!* when it filled: *booked · you paid* now
                # (Q110). At the club's yes, the club's yes is the news.
                booked_on_a_payment=bool(proposal.paying) and not asked,
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
                asked=asked,
                now=now,
            )

        first_side, second_side = (
            sides if sides is not None else await self._sides(proposal)
        )
        proposal.fill(first_side=first_side, second_side=second_side, by=by, at=now)
        game_id = await book(first_side, second_side)
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
        asked: bool,
        now: Instant,
    ) -> FillOutcome:
        """Nobody paid. **Each refused share's player has until ``pay_by``**,
        their seat held for them alone — to fix the card or to pay
        (``time_to``, #638) — and, at the club's yes, the yes and its court
        kept (#626). With no time left — the club said yes past the book-by —
        the seats reopen and the game is called off at once."""

        payers = tuple(sorted(refused, key=str))
        if pay_by is None:
            for player in payers:
                proposal.reopen_seat(
                    player,
                    reason=ReopenReason(refused[player].refusal.value),
                    seat_charge_id=refused[player].seat_charge_id,
                    at=now,
                )
            if asked:
                await self._requests.payment_not_in_time(
                    proposal.proposal_id, player_ids=payers, for_good=True, at=now
                )
            return FillOutcome(refused=refused, called_off=asked)
        already = bool(proposal.paying)
        for player in payers:
            proposal.give_time_to_pay(
                player,
                reason=ReopenReason(refused[player].refusal.value),
                seat_charge_id=refused[player].seat_charge_id,
                until=pay_by,
                time_to=time_to,
                filled_by=by,
                at_the_clubs_yes=asked,
                at=now,
            )
        if asked and not already:
            # The club's yes is kept, and its court, while the payment comes.
            await self._requests.await_a_payment(
                proposal.proposal_id,
                player_ids=payers,
                until=pay_by,
                to_fix_the_card=time_to is TimeTo.FIX_THE_CARD,
                at=now,
            )
        return FillOutcome(
            refused=refused, paying_until=proposal.pay_by, time_to=proposal.time_to
        )

    async def _withdraw_the_request(
        self, proposal: Proposal, opened: Collection[UUID], *, now: Instant
    ) -> None:
        """Seats opened on a game that waited for its club: the request is off."""

        await self._requests.withdraw(
            proposal.proposal_id, player_ids=tuple(sorted(opened, key=str)), at=now
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
                was_with_its_club = other.with_its_club
                was_paying = dict(other.paying)
                if same_hour:
                    # Not their own act: nobody is told whose hour it was.
                    other.withdraw_yes(player, at=now, own=False)
                else:
                    other.pause_yes(player, at=now)
                await self._proposals.save(other)
                if was_with_its_club and not other.with_its_club:
                    # A game of theirs that waited for its club is off.
                    await self._withdraw_the_request(other, (player,), now=now)
                await let_go_of_what_was_kept(
                    other, was_paying, leaver=player, undecided=self._undecided, at=now
                )
