"""A player's three answers to a card: **yes**, **no**, and a yes taken back
(the mechanics §6, §10.2; the screens A2.4, A3.2).

**All three are silent.** Nothing here is told to anybody: the others learn of a
yes from the card, and a no leaves no trace but the card's absence (§6.4). Each
is one transaction on one stream, and a repeated tap records nothing.

**A yes asks the game first, then the player's account, then the people In** —
a stranger learns nothing about anybody's card, a player with no method is sent
to save one before a live yes is counted, and whether they still fit the people
In is the last thing asked because it is the only question that costs reads of
other people.

**The yes that leaves no seat open books the game** (#541, ``fill.py``): every
seat charged together or nobody, in this yes's own transaction — and the game's
row is locked first, so two last yeses arriving together fill it once. The
client gave its ten seconds of *Undo* before sending it — or, at an On request
club, puts the full game to the club, and nobody pays until it says yes (#543).
**Confirming a refused payment is the yes again** (``ConfirmPayment``): the
player's share is held now, so the game fills on it if the seat is still theirs
to take. **Within their time to pay** (#625, #626) the seat is theirs alone and
they are still In: confirming books the game at once on the holds the others
kept — at the club's yes, without asking the club again — or, a seat having
opened meanwhile, leaves them In with their payment held. **Past it** their
time is run out first, as the job would have (``time_to_pay.py``), and the
confirmation is a yes on a reopened seat.

**A member may join a post from the slot sheet** (#546; Q79): their yes on a
post they were never dealt — held to everything a yes is, and to who the post
is for. Only a post: a pick is a stranger's to nobody but the people it names.

**Withdrawing is leaving, while the club decides** (the mechanics §13): a yes
taken back from a game waiting for its club takes the request with it — called
off with nobody paid, the court free, and the game filling again with that seat
open.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Protocol, final
from uuid import UUID

from app.application.ports import UnitOfWork
from app.kernel import Clock, Instant, instant
from app.modules.proposals.application.commands import (
    AnswerProposalCommand,
    ConfirmPaymentCommand,
)
from app.modules.proposals.application.fill import Booked, Fill, FillOutcome
from app.modules.proposals.application.guards import Guards
from app.modules.proposals.application.making import loaded
from app.modules.proposals.application.time_to_pay import (
    let_go_of_what_was_kept,
    run_out_if_due,
    run_out_the_cards_to_fix,
)
from app.modules.proposals.domain.errors import (
    BookingIsCalledOff,
    BookingNotFound,
    CourtJustTaken,
    GameHasStarted,
    PaymentToConfirm,
    ProposalIsFull,
    ProposalIsOver,
    ProposalNotFound,
    RescueNotOffered,
    SeatJustTaken,
)
from app.modules.proposals.domain.ports import (
    BookedGameChanges,
    CardsToFix,
    ClubRequests,
    PlayerBookings,
    ProposalRepository,
    RefusedPayment,
    SeatCharges,
    UndecidedCharges,
)
from app.modules.proposals.domain.proposal import Origin, Proposal, Standing, TimeTo


@final
@dataclass(frozen=True, slots=True)
class YesAnswer:
    """What a yes left: the seats still open on the game — nought for a game
    every seat said yes to — and, when it was the last, what the fill did."""

    proposal_id: UUID
    open_seats: int
    #: The game this yes booked — *It's a game!*
    booked: Booked | None = None
    #: This yes filled the game at an On request club, which has until then to
    #: answer — nobody pays until it says yes.
    waiting_until: Instant | None = None
    #: This player's own share could not be held: nobody paid, and the payment
    #: is theirs to confirm.
    your_payment: RefusedPayment | None = None
    #: The game waits for a refused payment until then — this player's own, or
    #: somebody else's (#625, #626): *Waiting for one payment · until 14:40*.
    paying_until: Instant | None = None
    #: What that time is for — to fix the card, or to pay (#638).
    time_to: TimeTo | None = None


@final
class SayYes:
    def __init__(
        self,
        *,
        proposals: ProposalRepository,
        guards: Guards,
        fill: Fill,
        requests: ClubRequests,
        undecided: UndecidedCharges,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._proposals = proposals
        self._guards = guards
        self._fill = fill
        self._requests = requests
        self._undecided = undecided
        self._uow = uow
        self._clock = clock

    async def execute(self, command: AnswerProposalCommand) -> YesAnswer:
        return await _a_court_taken_tried_again(
            lambda: self._once(command), uow=self._uow
        )

    async def _once(self, command: AnswerProposalCommand) -> YesAnswer:
        now = instant(self._clock.now())
        player_id = command.player_id
        proposal = await _locked(self._proposals, command.proposal_id)
        await run_out_if_due(
            proposal,
            player_id,
            proposals=self._proposals,
            requests=self._requests,
            undecided=self._undecided,
            now=now,
        )
        if player_id in proposal.paying:
            return await self._paying_again(proposal, player_id, now=now)
        outcome = FillOutcome()
        # Joining a post from the slot sheet: a yes from somebody it was never
        # dealt to.
        joining = proposal.origin is Origin.POST and not proposal.is_on_it(player_id)
        may = proposal.may_join if joining else proposal.may_say_yes
        if may(player_id, at=now):
            reopened = proposal.reopened.get(player_id)
            if reopened is not None and reopened.payment_to_confirm is not None:
                # Their seat reopened on a payment the bank wants confirmed, or
                # declined: asking it again off-session meets the same answer.
                # Confirming that payment is their yes again.
                raise PaymentToConfirm(
                    seat_charge_id=str(reopened.payment_to_confirm)
                )
            outcome = await _yes(
                proposal,
                player_id,
                guards=self._guards,
                fill=self._fill,
                now=now,
                joining=joining,
            )
            await self._proposals.save(proposal)
            await self._uow.commit()
        return _answer(proposal, player_id, outcome)

    async def _paying_again(
        self, proposal: Proposal, player_id: UUID, *, now: Instant
    ) -> YesAnswer:
        """A yes from a player whose time to pay runs (#625): a refused payment
        is confirmed, never asked again — the bank would be asked the same
        question; terms accepted again, or a method saved, is their payment
        tried now, on the holds the others kept."""

        paying = proposal.paying[player_id]
        if paying.payment_to_confirm is not None:
            raise PaymentToConfirm(seat_charge_id=str(paying.payment_to_confirm))
        await self._guards.refuse_an_unchargeable_yes(player_id)
        outcome = await _paid_in_time(
            proposal,
            player_id,
            fill=self._fill,
            undecided=self._undecided,
            now=now,
        )
        await self._proposals.save(proposal)
        await self._uow.commit()
        return _answer(proposal, player_id, outcome)


async def _paid_in_time(
    proposal: Proposal,
    player_id: UUID,
    *,
    fill: Fill,
    undecided: UndecidedCharges,
    now: Instant,
) -> FillOutcome:
    """This payer's share can be held now, within their time: the game books on
    it and the holds the others kept, if it waits for nobody else's payment and
    every seat is In; otherwise they are In with their payment held, and the
    seat theirs — and once nobody's payment is awaited, what was kept for the
    wait is let go. **No commit.**"""

    was_paying = dict(proposal.paying)
    if proposal.waiting_for_a_payment and set(proposal.paying) == {player_id}:
        outcome = await fill.run(proposal, by=player_id, now=now)
    else:
        outcome = FillOutcome()
    if (
        outcome.booked is None
        and player_id not in outcome.refused
        and proposal.ending is None
        and player_id in proposal.paying
    ):
        proposal.time_to_pay_met(player_id, at=now)
    await let_go_of_what_was_kept(proposal, was_paying, undecided=undecided, at=now)
    return outcome


class JoinsARescue(Protocol):
    """Taking an open seat on a booked game (#545) — ``rescues.py``'s
    ``Rescuer``, declared here so a confirmed rescue payment reaches it
    without the two modules importing each other."""

    async def join(
        self,
        proposal: Proposal | None,
        booking_id: UUID,
        player: UUID,
        *,
        now: Instant,
        confirmed: UUID | None = None,
    ) -> YesAnswer: ...


@final
class ConfirmPayment:
    """*I confirmed my payment in the app* — **the yes again** (the mechanics
    §12.2). The refused payment is asked of the provider; held now, it is the
    player's share, and their yes lands on the game it was for — filling it, if
    theirs was the seat still open, with everybody else charged then.

    **Until somebody else takes the seat**: a game that filled without them, or
    whose seat somebody else took, or that is no longer filling, lets the hold
    go and answers as a yes would — ``proposal_is_over`` or ``proposal_is_full``.

    **On a booked game it is the join again** (#545): the payment was a
    rescue's, and the open seat is taken on it — unless somebody took it first
    (``seat_just_taken``), the game is off or has begun, or the seat is no
    longer theirs to be offered; then the hold is let go. **Or it is the card
    fixed** (#639): a holding refused on the player's own booked game, within
    their time to fix it, is held until the cut-off and their seat simply theirs
    again; past that time it runs out first — the seat open to others, nothing
    owed — and the confirmation is a leaver's, refused.
    """

    def __init__(
        self,
        *,
        proposals: ProposalRepository,
        guards: Guards,
        fill: Fill,
        charges: SeatCharges,
        undecided: UndecidedCharges,
        requests: ClubRequests,
        rescuer: JoinsARescue,
        bookings: PlayerBookings,
        games: BookedGameChanges,
        cards: CardsToFix,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._proposals = proposals
        self._guards = guards
        self._fill = fill
        self._charges = charges
        self._undecided = undecided
        self._requests = requests
        self._rescuer = rescuer
        self._bookings = bookings
        self._games = games
        self._cards = cards
        self._uow = uow
        self._clock = clock

    async def execute(self, command: ConfirmPaymentCommand) -> YesAnswer:
        return await _a_court_taken_tried_again(
            lambda: self._once(command), uow=self._uow
        )

    async def _once(self, command: ConfirmPaymentCommand) -> YesAnswer:
        now = instant(self._clock.now())
        player_id = command.player_id
        game_id = await self._charges.confirmed(
            command.seat_charge_id, player_id=player_id, at=now
        )
        proposal = await _locked(self._proposals, game_id)
        if proposal.standing_at(now) is Standing.FILLED:
            fixed = await self._card_fixed(
                proposal, player_id, confirmed=command.seat_charge_id, now=now
            )
            if fixed is not None:
                return fixed
            return await self._rescue(
                proposal, player_id, confirmed=command.seat_charge_id, now=now
            )
        await run_out_if_due(
            proposal,
            player_id,
            proposals=self._proposals,
            requests=self._requests,
            undecided=self._undecided,
            now=now,
        )
        if player_id in proposal.paying:
            # Paid within their time: the seat was theirs alone (#625, #626).
            outcome = await _paid_in_time(
                proposal,
                player_id,
                fill=self._fill,
                undecided=self._undecided,
                now=now,
            )
            await self._proposals.save(proposal)
            await self._uow.commit()
            return _answer(proposal, player_id, outcome)
        if player_id in proposal.yeses:
            # Confirmed and In already — a second tap, or the yes said again.
            await self._uow.commit()
            return _answer(proposal, player_id, FillOutcome())
        try:
            # Not In, so this either admits the yes or refuses it.
            proposal.may_say_yes(player_id, at=now)
        except (ProposalIsFull, ProposalIsOver):
            await self._too_late(proposal, player_id, now=now)
            raise
        outcome = await _yes(
            proposal, player_id, guards=self._guards, fill=self._fill, now=now
        )
        await self._proposals.save(proposal)
        await self._uow.commit()
        return _answer(proposal, player_id, outcome)

    async def _card_fixed(
        self, proposal: Proposal, player_id: UUID, *, confirmed: UUID, now: Instant
    ) -> YesAnswer | None:
        """The player's own booked game, whose holding of this payment was
        refused (#639): within their time, the share is held and the card
        fixed; past it, the time runs out first — and the confirmation goes on
        as one on a seat no longer theirs. ``None`` for any other payment."""

        game = await self._bookings.find(proposal.proposal_id)
        to_fix = None if game is None else game.cards_to_fix.get(player_id)
        if game is None or to_fix is None or to_fix.seat_charge_id != confirmed:
            return None
        if now >= to_fix.until:
            # Run out first, in this transaction and under this lock: the
            # confirmation goes on as a leaver's, which the rescue refuses —
            # and whose refusal commits the run-out with the hold let go.
            await run_out_the_cards_to_fix(
                proposal.proposal_id,
                bookings=self._bookings,
                games=self._games,
                cards=self._cards,
                now=now,
            )
            return None
        await self._cards.keep_fixed(confirmed, at=now)
        await self._games.card_fixed(proposal.proposal_id, player_id, at=now)
        await self._uow.commit()
        return YesAnswer(
            proposal_id=proposal.proposal_id,
            open_seats=game.open_seats,
            booked=None
            if game.game_id is None
            else Booked(booking_id=game.booking_id, game_id=game.game_id),
        )

    async def _rescue(
        self, proposal: Proposal, player_id: UUID, *, confirmed: UUID, now: Instant
    ) -> YesAnswer:
        """A booked game's payment: a rescue's, and confirming it takes the
        seat (#545)."""

        try:
            answer = await self._rescuer.join(
                proposal,
                proposal.proposal_id,
                player_id,
                now=now,
                confirmed=confirmed,
            )
        except (
            SeatJustTaken,
            BookingIsCalledOff,
            GameHasStarted,
            RescueNotOffered,
            BookingNotFound,
        ):
            await self._too_late(proposal, player_id, now=now)
            raise
        await self._uow.commit()
        return answer

    async def _too_late(
        self, proposal: Proposal, player_id: UUID, *, now: Instant
    ) -> None:
        """Somebody else took the seat, or the game is no longer filling: the
        hold this player confirmed is let go, and nobody pays it."""

        await self._undecided.release(
            proposal.proposal_id, keeping=(), of_player=player_id, at=now
        )
        await self._uow.commit()


async def _a_court_taken_tried_again(
    attempt: Callable[[], Awaitable[YesAnswer]], *, uow: UnitOfWork
) -> YesAnswer:
    """The yes, and once more if another game claimed its court a moment before
    (``CourtJustTaken``): the transaction is spent, so it is rolled back and the
    yes read again from the start — the courts left, the same holds answered
    again under the same keys. A second race in a row reaches the client."""

    try:
        return await attempt()
    except CourtJustTaken:
        await uow.rollback()
        return await attempt()


async def _locked(proposals: ProposalRepository, proposal_id: UUID) -> Proposal:
    proposal = await proposals.load_for_update(proposal_id)
    if proposal is None:
        raise ProposalNotFound()
    return proposal


async def _yes(
    proposal: Proposal,
    player_id: UUID,
    *,
    guards: Guards,
    fill: Fill,
    now: Instant,
    joining: bool = False,
) -> FillOutcome:
    """The yes itself, after its guards — and the fill, when it was the last.
    ``joining`` a post from the slot sheet, it is a yes from outside its
    versions."""

    # Somebody who has left the group has left its pool: the card is nothing to
    # them any more, which is the stranger's answer.
    if not await guards.in_the_pool(proposal.pool, [player_id]):
        raise ProposalNotFound()
    await guards.refuse_an_unchargeable_yes(player_id)
    if joining:
        await guards.refuse_a_join_dealing_would_not_make(player_id, proposal, now=now)
    await guards.refuse_a_yes_that_does_not_fit(player_id, proposal, at=now)
    await guards.refuse_a_yes_the_post_is_not_for(player_id, proposal)
    if joining:
        proposal.join(player_id, at=now)
    else:
        proposal.say_yes(player_id, at=now)
    if proposal.open_seats > 0:
        return FillOutcome()
    return await fill.run(proposal, by=player_id, now=now)


def _answer(proposal: Proposal, player_id: UUID, outcome: FillOutcome) -> YesAnswer:
    if outcome.court_lost:
        raise ProposalIsOver(standing=Standing.COURT_HOUR_LOST.value)
    return YesAnswer(
        proposal_id=proposal.proposal_id,
        open_seats=proposal.open_seats,
        booked=outcome.booked,
        waiting_until=outcome.waiting_until,
        your_payment=outcome.refused.get(player_id),
        paying_until=outcome.paying_until,
        time_to=outcome.time_to,
    )


@final
class SayNo:
    def __init__(
        self, *, proposals: ProposalRepository, uow: UnitOfWork, clock: Clock
    ) -> None:
        self._proposals = proposals
        self._uow = uow
        self._clock = clock

    async def execute(self, command: AnswerProposalCommand) -> None:
        proposal = await loaded(self._proposals, command.proposal_id)
        proposal.say_no(command.player_id, at=instant(self._clock.now()))
        await self._proposals.save(proposal)
        await self._uow.commit()


@final
class WithdrawYes:
    """*Withdraw* on a You're In row: free and silent until the game fills —
    and *Leave the game* while its club decides, which takes the request to the
    club with it. **Not asked of the pool** — somebody who left the group can
    still take a yes back that is theirs.

    The game is read **locked**, as a yes reads it, so a leaving and the club's
    yes arriving together are one after the other."""

    def __init__(
        self,
        *,
        proposals: ProposalRepository,
        requests: ClubRequests,
        undecided: UndecidedCharges,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._proposals = proposals
        self._requests = requests
        self._undecided = undecided
        self._uow = uow
        self._clock = clock

    async def execute(self, command: AnswerProposalCommand) -> None:
        now = instant(self._clock.now())
        proposal = await _locked(self._proposals, command.proposal_id)
        await withdraw_a_yes(
            proposal,
            command.player_id,
            proposals=self._proposals,
            requests=self._requests,
            undecided=self._undecided,
            at=now,
        )
        await self._uow.commit()


async def withdraw_a_yes(
    proposal: Proposal,
    player_id: UUID,
    *,
    proposals: ProposalRepository,
    requests: ClubRequests,
    undecided: UndecidedCharges,
    at: Instant,
) -> None:
    """The yes taken back — and, when it was a seat of a game its club has,
    the request to the club with it (#543), so the held court is free the
    moment the seat is; at the club's yes, the yes with it (#626). **A leave
    from a game waiting for a payment** lets the leaver's hold go, and the
    payer's time runs on (#625). **No commit.**"""

    was_with_its_club = proposal.with_its_club
    was_paying = dict(proposal.paying)
    proposal.withdraw_yes(player_id, at=at)
    await proposals.save(proposal)
    if was_with_its_club and not proposal.with_its_club:
        # Their own act: the others are told who left (Q104).
        await requests.withdraw(
            proposal.proposal_id, player_ids=(player_id,), left=(player_id,), at=at
        )
    await let_go_of_what_was_kept(
        proposal, was_paying, undecided=undecided, at=at, leaver=player_id
    )
