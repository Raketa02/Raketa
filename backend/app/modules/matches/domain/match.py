"""The Match aggregate: a record with a version, an outbox, and no history.

ADR-0034, and it is the fourth of ADR-0002's five per-context choices to be made
— the first that has come out *against* event sourcing, which is what a genuinely
per-context rule looks like when it is real. Not sourced, because *"almost
nothing about a match is stored"* and the home screen reads several of them on
every open: rebuilding each from a stream is the cost ADR-0017 warned about, and
it buys nothing for concurrency that a version on a row does not already buy. Not
a row plus an audit log either, which is the dual write ADR-0017 refused.

**One aggregate.** *Enrolled* is a relationship and not an object: a seat names a
player or it does not (``seat.py``). A second aggregate for the enrolled view
would encode a fact about a player's relationship as a fact about the match,
which is the mistake ADR-0030 named.

**Five kinds of stored fact**, and every field below is filed under the question
ADR-0034 classifies by — *may a reader derive this, or may only a writer produce
it?* Nothing derived is stored: how full the match is, whether a court is held,
whether it has been played and the situation itself are all computed from these
facts and the clock, every time. A new fact has to declare its kind before it can
be added, and *"a reader cannot derive this"* has to be true of it.

**Two facts ADR-0034's table names and this record deliberately does not carry.**

- ``courtId``. ADR-0035 landed after ADR-0034 and put the court on the
  reservation, where a caller *"never learns how courts are organised"*: the
  reservation already says ``MatchHeld(match_id)``, so a column here would be the
  same arrow drawn twice and two places for it to disagree — the argument that
  keeps a `padded` flag off a reservation and an interval off a booking. What is
  the match's own is *whether* a court is being held, which is ``held_since`` and
  ``released_at``, and that is what the ladder reads. *Which* court is a query
  over reservations, and a reader can derive it, which is exactly the test the
  five kinds apply.
- ``holdKind`` and ``protectedAt``. The kernel **composes** a hold from the
  record (``kernel.court_hold``), so storing its answer would be a second
  spelling of a computation — and ADR-0071 is the rule that a field with no
  reader is not forwards-compatibility, it is a field nobody maintains. The hold
  ladder is ``Raketa02/Raketa#71``; when it needs a fact this record cannot
  state, it adds it here with its kind declared.

**The policy snapshot is Constitutive, and that is a decision worth reading.**
ADR-0077 puts a club value that must be honoured *as booked* — the cancellation
window in force when a player committed — *"on the match record as a Constitutive
fact, not in a temporal query, so no state on Now inherits another aggregate's
fold."* So the four fields the ladder reads are copied at posting and travel with
the match, which is also what makes ``as_record`` need **no other read**: one
row-set in, a situation out, no club fetch on the busiest path in the product.
The cost is real and is stated rather than hidden — a club that tightens its cap
does not reach a match already posted. If ``Raketa02/Raketa#71`` decides it must,
the fix is a **write** that refreshes this snapshot, with an announcement of its
own, and never a club read on the compose path.

**Every change announces itself, specifically** (``events.py``). The match keeps
no history, so the outbox trail *is* the record of what happened, and a generic
*match updated* would be the one thing that makes it useless.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import final
from uuid import UUID, uuid5

from app.kernel import (
    SPORT_SPECS,
    HoldPolicy,
    Instant,
    LeaverMoney,
    MatchKind,
    MatchRecord,
    Minutes,
    NothingTaken,
    Outcome,
    PayModel,
    Recoverable,
    SeatShare,
    Sport,
    committed_on_fill,
    deadlines,
    is_full,
    is_terminal,
    keeping_a_court,
    live_outcome,
    match_end,
    outcome_worse_than,
    refill_outcome,
    result_window,
)
from app.shared.domain import DomainEvent, EventRecorder

from app.modules.matches.domain.departure import (
    Departure,
    born_settled,
    oldest_unsettled,
)
from app.modules.matches.domain.errors import (
    CourtAlreadyHeld,
    DepartureOutcomeWorsened,
    MatchAlreadySettled,
    MatchAlreadyStarted,
    MatchIsFull,
    MatchNotPlayed,
    MatchNotPrivate,
    NoCourtHeld,
    NoScoreOnTheTable,
    PlayerAlreadyHoldsASeat,
    ResultAlreadyAgreed,
    ResultWindowClosed,
    SeatNotFound,
    SeatNotTaken,
    StartMustBeInTheFuture,
)
from app.modules.matches.domain.events import (
    CourtHeld,
    CourtLocked,
    CourtReleased,
    DepartureOutcomeImproved,
    DepartureSettled,
    HoldExtended,
    InventoryLost,
    MatchCancelledAtCheckpoint,
    MatchCancelledByClub,
    MatchCancelledForWeather,
    MatchCancelledIncomplete,
    MatchCommitted,
    MatchPosted,
    MatchStartMoved,
    NoShowRecorded,
    PlayerDeparted,
    ResultAgreed,
    ScoreProposed,
    SeatPaid,
    SeatsOpened,
    SeatTaken,
    SeatTransferEnded,
    SeatTransferStarted,
    SeatVacated,
)
from app.modules.matches.domain.score import Score
from app.modules.matches.domain.seat import Seat
from app.modules.matches.domain.vacancy import Vacancy


@final
@dataclass
class Match:
    """One match: what was posted, who is on it, and what has happened since.

    ``version`` is the **stored** row version and is not touched here — the
    repository compares it on the way out and bumps it, the same split ``Club``
    and ``Reservation`` make. An aggregate that incremented its own would have
    to be told what the store did next, and the two counters would be one fact
    in two places.
    """

    id: UUID

    # -- Constitutive · chosen at creation, never recomputed ----------------
    # A reader cannot derive any of these because nobody computed them: they
    # were *chosen*, by whoever posted the match.
    club_id: UUID
    category_id: UUID
    sport: Sport
    duration: Minutes
    share: SeatShare
    counted: bool
    created: Instant
    kind: MatchKind
    pay_model: PayModel
    policy: HoldPolicy

    #: **Deliberately not constitutive.** ADR-0032 keeps it mutable and *"a
    #: moved match is the same match"*; every deadline is relative to it, so
    #: moving it moves all five at once.
    start: Instant

    # -- Occupancy · current state, freely reversible -----------------------
    # Not derivable — but nothing derives *from* absence either, which is what
    # makes them safe to move in both directions.
    seats: list[Seat] = field(default_factory=list)
    vacancies: list[Vacancy] = field(default_factory=list)

    #: The leavers. **Beside the vacancies and never folded into them** — a hole
    #: and a settlement are two facts on two axes (ADR-0033), and the one field
    #: they share is the seat. Occupancy by kind, because a departure is
    #: underivable from every direction: the seat it emptied says nothing about
    #: who left, and a refilled seat says nothing at all. Its ``outcome`` is the
    #: exception and behaves like a Crossing — once it is decided it may only
    #: improve, and ``Departure`` has no operation that lowers it.
    departures: list[Departure] = field(default_factory=list)

    transferring: bool = False

    #: How many of a private court's seats are on the marketplace. A Declaration
    #: in effect — opening one takes unanimous consent from everybody already
    #: paid (ADR-0030), and no reader can derive that a group agreed to sell.
    open_seats: int = 0

    # -- Allocation · a claim on contended inventory, and its failure -------
    # A court is a scarce resource, not a computation.
    held_since: Instant | None = None
    released_at: Instant | None = None
    inventory_lost: bool = False

    # -- Crossing · a threshold irreversibly passed -------------------------
    # Derivable **once**, then frozen, because the inputs stop supporting it:
    # commitment needs the deadline passed *and* the match full, so re-deriving
    # it would release three people the moment a fourth left.
    committed_at: Instant | None = None

    # -- Declaration · an outside actor's decision --------------------------
    # No reader can derive any of these, by construction.
    court_locked: bool = False
    club_extended: bool = False
    club_cancelled: bool = False
    weather: bool = False
    no_show: bool = False
    score: Score | None = None
    score_by: UUID | None = None
    proposals: int = 0
    result_agreed: bool = False

    #: The two **receipts**, and they are an annotation rather than a sixth kind
    #: (ADR-0034). The situation derives without them — a match short at its
    #: checkpoint is cancelled whether or not anybody has processed it — and the
    #: flag records only that the refund, the court release and the notice
    #: completed. That is what makes a downed timekeeper delay the money and
    #: never the truth.
    form_cancelled: bool = False
    checkpoint_cancelled: bool = False

    version: int = 0

    _events: EventRecorder = field(
        default_factory=EventRecorder, init=False, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        players = SPORT_SPECS[self.sport].players
        if len(self.seats) != players:
            raise ValueError(
                f"{self.sport.value} is sold in {players} seats, "
                f"not {len(self.seats)}"
            )
        if [seat.index for seat in self.seats] != list(range(players)):
            raise ValueError("seats are numbered 0..n-1 in a fixed order")
        if not 0 <= self.open_seats <= players:
            raise ValueError(f"{self.open_seats} seats opened of {players}")

    # -- posting ------------------------------------------------------------

    @classmethod
    def post(
        cls,
        *,
        match_id: UUID,
        club_id: UUID,
        category_id: UUID,
        sport: Sport,
        start: Instant,
        duration: Minutes,
        share: SeatShare,
        policy: HoldPolicy,
        at: Instant,
        counted: bool = True,
        kind: MatchKind = MatchKind.OPEN,
        pay_model: PayModel = PayModel.SPLIT,
        open_seats: int = 0,
    ) -> "Match":
        """A new match, with every seat the sport is sold for, all of them empty.

        The seats exist from the first instant: the sport decides how many there
        are, so they are never created or destroyed and *how full is this* is a
        count over a fixed list rather than a stored number.
        """

        players = SPORT_SPECS[sport].players
        match = cls(
            id=match_id,
            club_id=club_id,
            category_id=category_id,
            sport=sport,
            duration=duration,
            share=share,
            counted=counted,
            created=at,
            kind=kind,
            pay_model=pay_model,
            policy=policy,
            start=start,
            seats=[Seat(index=index) for index in range(players)],
            open_seats=open_seats,
        )
        match._record(
            MatchPosted(
                match_id=match.id,
                club_id=club_id,
                category_id=category_id,
                sport=sport.value,
                kind=kind.value,
                pay_model=pay_model.value,
                start=start,
                duration_minutes=int(duration),
                seats=players,
                share_grosze=int(share),
                counted=counted,
                policy_window_minutes=int(policy.window),
                policy_join_cut_minutes=int(policy.join_cut),
                occurred_at=at,
            )
        )
        return match

    # -- the record the ladder reads ----------------------------------------

    def as_record(self) -> MatchRecord:
        """Every stored fact the kernel reads, and **no other read**.

        This is the whole of ADR-0034's *"the busiest object in the product is
        the cheapest to read"*: one row-set in, a `MatchRecord` out, and
        `kernel.situation` answers from it with no club fetch, no reservation
        lookup and no rehydration between the read and the answer.
        """

        return MatchRecord(
            sport=self.sport,
            start=self.start,
            duration=self.duration,
            created=self.created,
            seats=tuple(seat.as_record() for seat in self.seats),
            policy=self.policy,
            kind=self.kind,
            pay_model=self.pay_model,
            open_seats=self.open_seats,
            held_since=self.held_since,
            released_at=self.released_at,
            committed_at=self.committed_at,
            open_vacancies=tuple(
                vacancy.as_record() for vacancy in self.open_vacancies
            ),
            transferring=self.transferring,
            court_locked=self.court_locked,
            club_extended=self.club_extended,
            inventory_lost=self.inventory_lost,
            club_cancelled=self.club_cancelled,
            weather=self.weather,
            form_cancelled=self.form_cancelled,
            checkpoint_cancelled=self.checkpoint_cancelled,
            no_show=self.no_show,
            score_proposed=self.score is not None and not self.result_agreed,
            result_agreed=self.result_agreed,
        )

    @property
    def open_vacancies(self) -> list[Vacancy]:
        """The holes that are still holes, oldest first."""

        return sorted(
            (vacancy for vacancy in self.vacancies if vacancy.is_open),
            key=lambda vacancy: vacancy.vacated_at,
        )

    @property
    def is_settled(self) -> bool:
        """Whether nothing further can happen — the five endings, via the kernel."""

        return is_terminal(self.as_record())

    def seat_of(self, player_id: UUID) -> Seat | None:
        """The seat this player holds, if any. One player holds at most one."""

        for seat in self.seats:
            if seat.player_id == player_id:
                return seat
        return None

    def seat_at(self, index: int) -> Seat:
        for seat in self.seats:
            if seat.index == index:
                return seat
        raise SeatNotFound()

    def departure_of(self, player_id: UUID) -> Departure | None:
        """This player's departure, if she made one. The newest, if several.

        A leaver's card is looked up by *her*, not by a seat: the seat she left
        may be somebody else's by now, and ADR-0030's whole point is that her
        card survives the refill.
        """

        hers = [one for one in self.departures if one.player_id == player_id]
        if not hers:
            return None
        return max(hers, key=lambda one: (one.departed_at, one.seat_index))

    # -- the mutable start --------------------------------------------------

    def move_start(self, to: Instant, *, at: Instant) -> None:
        """Move the match. An ordinary write, with an announcement of its own.

        Every deadline is relative to ``start``, so all five move together and
        none of them is stored — which is what makes this a one-field write
        rather than a recomputation.
        """

        self._refuse_if_settled()
        self._refuse_if_started(at)
        if to <= at:
            raise StartMustBeInTheFuture()
        moved_from = self.start
        if to == moved_from:
            return
        self.start = to
        self._record(
            MatchStartMoved(
                match_id=self.id,
                moved_from=moved_from,
                moved_to=to,
                occurred_at=at,
            )
        )

    # -- occupancy ----------------------------------------------------------

    def take_seat(self, player_id: UUID, *, at: Instant) -> Seat:
        """A player takes the first free seat, holding it and owing for it.

        **The join cutoff is not enforced here.** ``Raketa02/Raketa#68`` fixes
        that a seat claim already running when ``joinCut`` passes is honoured to
        completion and only a *new* one is refused — so the gate belongs to the
        claim, and putting it here would make a deadline a trapdoor under a
        player who is already paying.

        Taking a seat closes the **oldest** open hole if there is one. Oldest
        rather than newest on purpose: two departures thirty hours and one hour
        ago, with one filler, is a match that lost somebody an hour ago and is
        still short — and the newest vacancy is what says so.

        It also settles the **oldest unsettled departure**, and ADR-0033 is
        emphatic that those are two traversals and not one: *"a filler closes
        the oldest open vacancy and settles the oldest unsettled departure, and
        those are not always the same departure."* The worked example is a
        transfer — born settled, hole open — followed by an ordinary leave: one
        sorted pass stopping at the first match hands the filler to the
        departure with nothing to settle, and the only person waiting on money
        is skipped. The symptom is *one player was never refunded*, months
        later, and never an error.
        """

        self._refuse_if_settled()
        self._refuse_if_started(at)
        if self.seat_of(player_id) is not None:
            raise PlayerAlreadyHoldsASeat()
        free = [seat for seat in self.seats if seat.is_free]
        if not free:
            raise MatchIsFull()

        seat = free[0]
        seat.take(player_id, at=at)
        holes = self.open_vacancies
        filled_a_vacancy = bool(holes)
        if filled_a_vacancy:
            holes[0].fill(at=at)
        self._record(
            SeatTaken(
                match_id=self.id,
                seat_index=seat.index,
                player_id=player_id,
                filled_a_vacancy=filled_a_vacancy,
                occurred_at=at,
            )
        )
        self._settle_the_longest_wait(at=at)
        return seat

    def pay_seat(self, player_id: UUID, *, at: Instant) -> Seat:
        """The money for this player's seat landed, and the match may now commit.

        Commitment is checked here rather than left to the timekeeper because a
        match that fills after its own deadline commits *the moment it fills*
        (``kernel.committed_on_fill``) — and a match that is bound to four
        people only once a scheduled job notices is the reassuring-direction
        failure ADR-0034's five kinds exist to remove.
        """

        self._refuse_if_settled()
        seat = self.seat_of(player_id)
        if seat is None:
            raise SeatNotTaken()
        seat.pay()
        self._record(
            SeatPaid(
                match_id=self.id,
                seat_index=seat.index,
                player_id=player_id,
                share_grosze=int(self.share),
                occurred_at=at,
            )
        )
        self.commit_if_due(at=at)
        return seat

    def depart(
        self, player_id: UUID, *, quote: Outcome, at: Instant
    ) -> Departure:
        """A player leaves: one hole in the match, one departure of her own.

        **Two records because they are two facts** (ADR-0033). The hole is what
        the ladder reads — *is this match short a player* — and it closes when
        anybody takes the seat. The departure is what her card reads — *is my
        money decided* — and it closes when no further seat event can change it.
        Neither implies the other, and welding them is what a single ``vacated``
        scalar did.

        **The quote is checked here and it is a comparison of labels.** She was
        shown what leaving is worth as the basis for the decision, so an outcome
        that has become *strictly worse* between the tap and the apply is
        refused and she is re-presented (``DepartureOutcomeWorsened``). Equal or
        better applies, which is what makes a forfeit quoted against a reversal
        pass: the quote protects money and in both cases the money is nothing.
        This is the whole of how two concurrent leaves resolve — the sharp case
        being the first leave dropping the match below its checkpoint threshold
        and turning the second player's free reversal into a forfeit.

        **Which money form she gets follows what she actually put in**, and it
        is one of two payloads rather than one with an optional amount
        (ADR-0072). A leave before the match committed clears the seat *and* the
        payment, so nothing was taken and the card can name no amount at all; so
        does a leave by somebody who held a seat and never paid for it. Either
        way the departure is **born settled**, because there is no money whose
        fate could still change.

        *A player who paid nothing may be quoted a refund and settle as a
        reversal, and that is not a contradiction: the quote is a fact about the
        match's phase, which is what the route printed, and her outcome is a
        fact about her money, which is nothing. The two agree about the only
        thing that matters.*
        """

        self._refuse_if_settled()
        self._refuse_if_started(at)
        seat = self.seat_of(player_id)
        if seat is None:
            raise SeatNotTaken()

        live = live_outcome(self.as_record(), at)
        if outcome_worse_than(live, quote):
            raise DepartureOutcomeWorsened(outcome=live)

        was_paid = seat.paid
        index = seat.index
        money: LeaverMoney = (
            Recoverable(amount=self.share)
            if was_paid and live is not Outcome.REVERSED
            else NothingTaken()
        )
        seat.vacate()

        vacancy = Vacancy(id=_vacancy_id(self.id, index, at), seat_index=index,
                          vacated_at=at)
        self.vacancies.append(vacancy)
        settled = born_settled(money)
        departure = Departure(
            id=_departure_id(self.id, index, at),
            seat_index=index,
            player_id=player_id,
            departed_at=at,
            quoted=live,
            money=money,
            outcome=Outcome.REVERSED if settled else None,
            settled_at=at if settled else None,
        )
        self.departures.append(departure)

        self._record(
            SeatVacated(
                match_id=self.id,
                seat_index=index,
                player_id=player_id,
                was_paid=was_paid,
                occurred_at=at,
            )
        )
        self._record(
            PlayerDeparted(
                match_id=self.id,
                departure_id=departure.id,
                seat_index=index,
                player_id=player_id,
                quoted=live.value,
                amount_grosze=(
                    None if isinstance(money, NothingTaken) else int(money.amount)
                ),
                occurred_at=at,
            )
        )
        if settled:
            self._announce_settlement(departure, at=at)
        return departure

    def resolve_departures_to(self, outcome: Outcome, *, at: Instant) -> int:
        """Move every departure to this outcome where that is **upward**.

        The fan-out ADR-0030's *"a club-side failure that refunds everybody may
        improve a settled 50 % to a full refund"* needs, and the only way an
        already-settled outcome ever moves. It is deliberately not a refusal
        when a departure is already at least this good: a cancellation reaches
        settled and unsettled departures alike, and *"you are still refunded in
        full"* is not a change anybody needs explained.

        Nothing here can lower an outcome, because ``Departure`` has no
        operation that does — the monotonicity is a property of the type rather
        than a rule this loop remembers. Ordered oldest first so the
        announcements a support agent reads are in the order the leavers left.

        Returns how many actually moved.
        """

        moved = 0
        for departure in sorted(
            self.departures, key=lambda one: (one.departed_at, one.seat_index)
        ):
            before = departure.outcome
            if not departure.raise_to(outcome, at=at):
                continue
            moved += 1
            if before is None:
                self._announce_settlement(departure, at=at)
            else:
                self._record(
                    DepartureOutcomeImproved(
                        match_id=self.id,
                        departure_id=departure.id,
                        player_id=departure.player_id,
                        improved_from=before.value,
                        improved_to=outcome.value,
                        occurred_at=at,
                    )
                )
        return moved

    def settle_departures_if_closed(self, *, at: Instant) -> int:
        """Forfeit whatever is still open once the roster can no longer change.

        **The definition is taken over the examples, and that is a departure
        from ADR-0030's wording worth reading.** It defines settlement as *"the
        moment no further **seat** event can change it"* and then illustrates
        that with *"at the checkpoint for a rebooking club, at the join cutoff
        for a standard one, never at match end."* This settles at the **start**,
        for two reasons.

        The definition is answerable here and the examples are not. ``start`` is
        the moment this aggregate refuses every seat move — ``_refuse_if_started``
        guards taking, leaving and moving the hour — so it is *derivably* the
        last instant a seat event can happen, where the join cutoff is a claim
        about a rule that lives somewhere else. And ADR-0081 landed after
        ADR-0030 and moved that rule: a seat claim already running when
        ``joinCut`` passes *"is honoured to completion"*
        (``Raketa02/Raketa#68``), so the cutoff stopped being the last seat
        event on the day claims were decided. Settling there would take money
        off a leaver whose seat was being paid for as the clock struck.

        Nobody is settled early by this, which is the only direction that
        matters: the start is later than both of ADR-0030's moments, an outcome
        may only ever improve, and a rebooking club's checkpoint cancellation
        forfeits its leavers earlier anyway through its own receipt. The club's
        ``rebookingCredit`` is not on this record — one of the four
        ``ClubPolicy`` fields the snapshot deliberately leaves behind — so the
        earlier of the two examples was never available here in any case.

        Forfeited rather than *whatever the phase says*: past the last seat
        event nobody can take the seat, so there is no money coming, and the
        phase agrees.

        A no-op before the start, and a no-op for a departure that took nothing.
        Returns how many moved.
        """

        if at < deadlines(self.as_record()).play:
            return 0
        return self.resolve_departures_to(Outcome.FORFEITED, at=at)

    def _settle_the_longest_wait(self, *, at: Instant) -> None:
        """The filler's half of ADR-0033's two queues. Never the same pass."""

        waiting = oldest_unsettled(self.departures)
        if waiting is None:
            return
        if waiting.raise_to(refill_outcome(self.as_record(), at), at=at):
            self._announce_settlement(waiting, at=at)

    def _announce_settlement(self, departure: Departure, *, at: Instant) -> None:
        outcome = departure.outcome
        if outcome is None:  # pragma: no cover - `raise_to` has just set it
            return
        self._record(
            DepartureSettled(
                match_id=self.id,
                departure_id=departure.id,
                player_id=departure.player_id,
                outcome=outcome.value,
                occurred_at=at,
            )
        )

    def open_seats_to_the_marketplace(self, count: int, *, at: Instant) -> None:
        """A private court puts ``count`` of its seats on sale.

        Unanimous among everybody already paid (ADR-0030) — that decision is the
        caller's to have taken; what is recorded here is that it was taken.
        """

        self._refuse_if_settled()
        if self.kind is not MatchKind.PRIVATE:
            raise MatchNotPrivate()
        if not 0 <= count <= len(self.seats):
            raise ValueError(f"{count} seats opened of {len(self.seats)}")
        if count == self.open_seats:
            return
        self.open_seats = count
        self._record(
            SeatsOpened(match_id=self.id, open_seats=count, occurred_at=at)
        )

    def begin_transfer(self, seat_index: int, *, at: Instant) -> None:
        """A leaver named somebody to take her seat; the handover is running.

        The **surface** for this does not exist in v1 — ``Raketa02/Raketa#91``
        says the departure screen mentions nothing about transferring a seat,
        because advertising a door that is not there is worse than the gap. The
        *fact* is read by the ladder (``replacementTransfer``), so the record
        can state it and this is how it comes to.
        """

        self._refuse_if_settled()
        seat = self.seat_at(seat_index)
        if not seat.is_taken:
            raise SeatNotTaken()
        if self.transferring:
            return
        self.transferring = True
        self._record(
            SeatTransferStarted(
                match_id=self.id, seat_index=seat_index, occurred_at=at
            )
        )

    def end_transfer(self, seat_index: int, *, at: Instant) -> None:
        """The handover finished or fell through, either way it is over."""

        self._refuse_if_settled()
        self.seat_at(seat_index)
        if not self.transferring:
            return
        self.transferring = False
        self._record(
            SeatTransferEnded(
                match_id=self.id, seat_index=seat_index, occurred_at=at
            )
        )

    # -- allocation ---------------------------------------------------------

    def hold_court(self, *, at: Instant) -> None:
        """A court is being kept aside for this match, from now.

        **When** a hold is granted is the ladder's question (ADR-0031,
        ``Raketa02/Raketa#71``); *that* one is held, and since when, is this
        record's fact — and it cannot be reconstructed, because nothing in the
        history distinguishes *the hold was granted at T* from *the second seat
        was paid at T* once a seat has been vacated and refilled.

        **Which** court is Courts' answer, keyed by ``MatchHeld(match_id)``.

        Granting again after a reclaim is ordinary and not a mistake: staleness
        is never latched, so a third payment closes the guard and the hold is
        live again. What is refused is granting one on top of a court this match
        is already keeping.
        """

        self._refuse_if_settled()
        if keeping_a_court(self.as_record()):
            raise CourtAlreadyHeld()
        self.held_since = at
        self.released_at = None
        self._record(CourtHeld(match_id=self.id, held_since=at, occurred_at=at))

    def release_court(self, *, at: Instant) -> None:
        """The court goes back on sale, and there is still a group to tell.

        **``held_since`` is left standing**, and that is the decision to read.
        The club's cap is measured from it, so a reclaim that also cleared it
        would reset the clock that had just fired — the ladder would grant again
        on the next look and reclaim again a cap later, for ever. ADR-0031 says
        *"cleared when it lapses"*; that and its own *"staleness is evaluated on
        the current facts, not latched"* cannot both hold of a stale reclaim, and
        the ladder above already reads it this way: ``heldReleased`` rewrites to
        ``heldStale``, which needs a court that has gone **and** a hold that
        still has an age. Certainty rising is what ends staleness, not
        forgetting how long we waited.

        ``released_at`` is a **receipt** — the notification was sent — and never
        the answer to *is a court held*, which the ladder computes.

        **The one write a settled match still makes**, and the exception is the
        rule working rather than a hole in it: the four cancellations each say in
        their own docstring that the court goes back, and a match that cancelled
        holding a court and could not release it would take that court out of the
        club's inventory for ever. Everything else about a settled match is
        refused, including holding a court in the first place.
        """

        if not keeping_a_court(self.as_record()):
            raise NoCourtHeld()
        self.released_at = at
        self._record(
            CourtReleased(match_id=self.id, released_at=at, occurred_at=at)
        )

    def lock_court(self, *, at: Instant) -> None:
        """The club committed a court by hand, outside the ladder."""

        self._refuse_if_settled()
        if self.court_locked:
            return
        self.court_locked = True
        self._record(CourtLocked(match_id=self.id, occurred_at=at))

    def extend_hold(self, *, at: Instant) -> None:
        """The club published an extension of a hold the ladder had lapsed."""

        self._refuse_if_settled()
        if self.club_extended:
            return
        self.club_extended = True
        self._record(HoldExtended(match_id=self.id, occurred_at=at))

    def lose_inventory(self, *, at: Instant) -> None:
        """The last court of the category went to somebody else. Terminal.

        One story and never *we raced somebody and lost*: ADR-0035 makes the
        race structurally impossible, so losing inventory is a query result
        (``Raketa02/Raketa#70``).
        """

        self._refuse_if_settled()
        self.inventory_lost = True
        self._record(InventoryLost(match_id=self.id, occurred_at=at))

    # -- crossing -----------------------------------------------------------

    def commit_if_due(self, *, at: Instant) -> bool:
        """Bind everybody to this match, if it is full and its deadline has come.

        Idempotent and one-directional: a match that has committed stays
        committed, because *"a re-derivation would release three people the
        moment a fourth left"*.
        """

        if self.committed_at is not None or self.is_settled:
            return False
        record = self.as_record()
        if not is_full(record) or at < deadlines(record).commit:
            return False
        self.committed_at = at
        self._record(
            MatchCommitted(
                match_id=self.id,
                committed_at=at,
                on_fill=committed_on_fill(self.as_record()),
                occurred_at=at,
            )
        )
        return True

    # -- declaration --------------------------------------------------------

    def cancel_by_club(self, *, at: Instant) -> None:
        """A manager cancelled it. **No reader can derive that**, which is why
        it is a Declaration and not one of the two receipts below.

        It refunds everybody, and *everybody* includes the people who already
        left: ADR-0030's own example of a settled outcome improving is *"a
        club-side failure that refunds everybody may improve a settled 50 % to a
        full refund."* A leaver settled at half whose match the club then lost
        gets the rest of her money, and she is the one person no card would ever
        have told.
        """

        self._refuse_if_settled()
        self.resolve_departures_to(Outcome.REFUNDED_IN_FULL, at=at)
        self.club_cancelled = True
        self._record(MatchCancelledByClub(match_id=self.id, occurred_at=at))

    def cancel_for_weather(self, *, at: Instant) -> None:
        """The weather took it. Its own story, told with its own name.

        Club-side in the sense that matters here — nobody who left caused it —
        so it reopens a settlement the same way a manager's cancellation does.
        """

        self._refuse_if_settled()
        self.resolve_departures_to(Outcome.REFUNDED_IN_FULL, at=at)
        self.weather = True
        self._record(MatchCancelledForWeather(match_id=self.id, occurred_at=at))

    def settle_incomplete_cancellation(self, *, at: Instant) -> None:
        """Record that a match which never filled has been refunded and released.

        A **receipt**, not a decision: the situation already derives — the
        deadline passed with the match short — and this says only that the money
        moved, the court went back and the notice went out.

        It resolves no departure, and that is not an omission: a match that
        never filled never committed, so every leave it saw was a reversal and
        every reversal is born settled with nothing to return.
        """

        self._refuse_if_settled()
        self.form_cancelled = True
        self._record(MatchCancelledIncomplete(match_id=self.id, occurred_at=at))

    def settle_checkpoint_cancellation(self, *, at: Instant) -> None:
        """The same receipt, for a match still short at its checkpoint.

        This is where a leaver forfeits, and it is the one outcome ADR-0030
        names as *"the only outcome where a player **who stayed** loses money"*
        having also been the one a leaver can land on. Nothing is lowered by it:
        forfeited ranks at the bottom, so a departure a filler already settled
        keeps whatever it settled at, and only the ones still open move.
        """

        self._refuse_if_settled()
        self.resolve_departures_to(Outcome.FORFEITED, at=at)
        self.checkpoint_cancelled = True
        self._record(MatchCancelledAtCheckpoint(match_id=self.id, occurred_at=at))

    def record_no_show(self, *, at: Instant) -> None:
        """Somebody who paid did not turn up."""

        self._refuse_if_settled()
        self._require_played(at)
        if self.no_show:
            return
        self.no_show = True
        self._record(NoShowRecorded(match_id=self.id, occurred_at=at))

    def propose_score(self, score: Score, *, by: UUID, at: Instant) -> None:
        """Put a score on the table, replacing whatever was there.

        Four facts and never a list (ADR-0034): the score on the table, who put
        it there, whether it is agreed, and **how many** proposals there have
        been. The conversation itself belongs to the announcements, which is the
        shape a support agent reads it in.

        Refused past ``kernel.result_window`` — the ladder answers
        ``playedNoScore`` from there, and a score stored past it would be one
        the screen cannot show. What the *route* asks and permits is
        ``Raketa02/Raketa#79``'s, including the permissive validator: nothing
        here judges whether 7-6 is a real set.
        """

        self._refuse_if_settled()
        self._require_played(at)
        if self.result_agreed:
            raise ResultAlreadyAgreed()
        if at >= result_window(self.as_record()):
            raise ResultWindowClosed()
        self.score = score
        self.score_by = by
        self.proposals += 1
        self._record(
            ScoreProposed(
                match_id=self.id,
                proposed_by=by,
                sets=[[one.side_a, one.side_b] for one in score.sets],
                proposals=self.proposals,
                occurred_at=at,
            )
        )

    def agree_result(self, *, at: Instant, by_silence: bool = False) -> None:
        """The score settles — by agreement, or by the silence that confirms it.

        ADR-0048 makes those one outcome and a support agent does not, so which
        one it was rides on the announcement and nowhere else.
        """

        self._refuse_if_settled()
        if self.result_agreed:
            raise ResultAlreadyAgreed()
        score = self.score
        if score is None:
            raise NoScoreOnTheTable()
        self.result_agreed = True
        self._record(
            ResultAgreed(
                match_id=self.id,
                sets=[[one.side_a, one.side_b] for one in score.sets],
                by_silence=by_silence,
                occurred_at=at,
            )
        )

    # -- events -------------------------------------------------------------

    def pull_events(self) -> list[DomainEvent]:
        """Everything this match has announced since it was last drained."""

        return self._events.pull()

    def _record(self, event: DomainEvent) -> None:
        self._events.record(event)

    # -- guards -------------------------------------------------------------

    def _refuse_if_settled(self) -> None:
        if self.is_settled:
            raise MatchAlreadySettled()

    def _refuse_if_started(self, at: Instant) -> None:
        if at >= self.start:
            raise MatchAlreadyStarted()

    def _require_played(self, at: Instant) -> None:
        if at < match_end(self.as_record()):
            raise MatchNotPlayed()


def _vacancy_id(match_id: UUID, seat_index: int, at: Instant) -> UUID:
    """A vacancy's id, derived rather than minted.

    Derived for the reason ADR-0019 derives an assessment's stream id: a
    domain layer that mints identifiers reaches for ``uuid4``, and a pure
    aggregate cannot. One match, one seat and one instant name one hole — the
    same seat emptied twice at one clock reading is not two holes.
    """

    return uuid5(match_id, f"vacancy:{seat_index}:{at.isoformat()}")


def _departure_id(match_id: UUID, seat_index: int, at: Instant) -> UUID:
    """A departure's id, derived the same way and from a different name.

    One match, one seat and one instant name one leaving — only one player can
    hold a seat, so there is nothing else it could be. The prefix is what keeps
    it distinct from the vacancy the same leaving opened: two records, two ids,
    from one pair of facts.
    """

    return uuid5(match_id, f"departure:{seat_index}:{at.isoformat()}")
