"""The Challenge aggregate — one game, its seats inside it, event-sourced.

**One aggregate per game, and never one per invitee.** A doubles send is one
Challenge containing four, not four challenges: the game is on only when the
*last* seat accepts, an accepted player may cross the net while their acceptance
stands, and the arrangement travels as a unit — three invariants that span every
seat at once, and four aggregates would need a saga to answer *is it on*.

**Identity is its own, minted, and deliberately not derived from the pair** the
way a Block's is. A four has no ordered pair to derive from, and the same people
may legitimately be challenged again later: that is a **new** challenge, not a
second version of an old one.

**Nothing here stores a standing.** ``standing_at`` folds the seats against a
clock the caller supplies, so *is this still open* answers the same at every
instant — including the whole gap between a deadline passing and a sweep noticing
it. The sweep (``lapse``) exists for the **record**, not for correctness.

**What it refuses** is in ``errors.py``, and the list is short on purpose:
answering a seat you do not hold, answering twice, answering after your own
deadline, challenging yourself, a challenge with no invitee, a court that is not
the sport's, removing somebody who is already in the game, a send with nobody
new to invite, a withdraw that is not the organiser's — or, on a court that has
been a game, not a player's on it — or is asked of a court somebody has joined,
of a game with no seat open, or of a challenge that has ended, an answer on a
challenge its organiser removed, and a departure from a seat that is not an
accepted one of yours, or from a court that has ended. Everything else this
context knows is derived.

**One act here announces its own conclusion, and exactly one may**
(``docs/adr/0142``). ``withdraw`` records the only standing no arrangement of the
seats could reach; every other transition changes a seat and lets the fold
answer.

**A yes can be taken back, and a court is over when one is left**
(``docs/adr/0165``). ``leave`` writes ``LEFT`` over an accepted seat on any
court that still stands — half built, awaiting, or a game (``docs/adr/0162``)
— and the fold re-derives what remains. **The ending rule is organiser-blind**:
a court is over when at most one player is on it and no seat is awaiting an
answer, and before a game that reaches the two endings the seats have, with a
departure counting as a no. A court that has been a game holds one fact beside
its seats — ``game_opened``, folded off the acceptance that completed its
line-up — because the fold must not end it the day one person is alone on it:
a game stands, and the departure that deserts it calls the game off one layer
up, in the same transaction, through the port the departure already uses. The
next completed line-up re-seats that game rather than opening another. **And
its other exit is the withdraw** (``docs/adr/0163``): a reopened court is
``LINE_UP_INCOMPLETE``, the withdraw is that standing's act, and the game is
called off one layer up — by any player on the court (``docs/adr/0165`` §5).
**On a court that was never a game the same act is *Remove the challenge***
(``docs/adr/0165`` §4): the organiser's, and admitted exactly while nobody
besides the organiser holds an accepted seat — before anybody answers, and
again once everybody who joined has left. A court somebody has joined is
nobody's to end for the others.

**What it does not refuse, and states as an invariant instead:** *an acceptance
is to the game, not to the side.* The membership is settled; the arrangement is
still the organiser's to choose, and ``invite`` is written to let exactly that
happen.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable, Mapping, Sequence
from uuid import UUID

from app.engines.matchfit.core import SearchMode
from app.kernel import Instant, Sport, instant, invariant
from app.modules.challenges.domain.answer_window import answer_by
from app.modules.challenges.domain.errors import (
    AChallengeNeedsAnInvitee,
    AnAcceptedPlayerMayNotBeRemoved,
    CannotChallengeYourself,
    NobodyIsAskedTwice,
    NobodyNewToInvite,
    NotYourSeat,
    OnePersonToASeat,
    OnlyAHalfBuiltLineUpIsWithdrawn,
    SomebodyHasJoinedTheCourt,
    TheAnswerWindowHasPassed,
    TheChallengeIsOver,
    TheCourtIsNotThisSports,
    TheOrganiserHoldsASeat,
    TheSeatIsAlreadyAnswered,
    TheWithdrawIsTheOrganisers,
)
from app.modules.challenges.domain.events import (
    ChallengeOpenedFromMutualInterest,
    ChallengeSent,
    ChallengeWithdrawn,
    SeatAccepted,
    SeatDeclined,
    SeatLapsed,
    SeatLeft,
    SeatsInvited,
)
from app.modules.challenges.domain.seats import (
    Seat,
    SeatAnswer,
    SeatPlan,
    Side,
    court_sides,
)
from app.modules.challenges.domain.standing import (
    ARRANGING,
    ENDED,
    Standing,
    deserted,
    ended_at_of,
    standing_of,
)
from app.modules.player_profile.domain.availability import Window
from app.shared.domain import DomainEvent
from app.shared.domain.events import EventRecorder


@dataclass
class Challenge:
    """One ask to play, rebuilt by folding its stream."""

    challenge_id: UUID
    sport: Sport
    #: The kind of evening this was sent for. ``None`` exactly when the send came
    #: from a surface with no mode — the deck — and on a mutual-born challenge
    #: where neither of the pair declared *for fun*; where either did, a
    #: mutual carries ``FOR_FUN`` (``docs/adr/0169`` §8), and never
    #: ``COMPETITIVE``.
    mode: SearchMode | None
    #: The window derived from the grid the search ran on, stamped at send.
    #: ``None`` on a mutual-born challenge: no grid was proposed from.
    window: Window | None
    organiser_id: UUID
    #: The court, in its fixed order — every ``A`` seat, then every ``B``.
    seats: tuple[Seat, ...]
    #: Everybody who has ever answered a seat on this challenge, including the
    #: ones whose seat has since been given to somebody else. **Nobody is asked
    #: twice**, and the seats alone cannot say so: a re-seated position forgets
    #: who left it, so the one place that remembers is here.
    answered: frozenset[UUID]
    opened_at: Instant
    updated_at: Instant
    #: When it was withdrawn — removed by the organiser, or called off by a
    #: player on the court it became — or ``None`` because it has not. **The one
    #: thing about a challenge that is not in its seats** — a decision somebody
    #: took, folded off ``ChallengeWithdrawn`` and read by ``standing_at`` before
    #: anything else.
    #:
    #: **An instant and no longer a bare ``bool``**
    #: ([#388](https://github.com/Raketa02/Raketa/issues/388)). It was a ``bool``
    #: on the argument that a moment belongs to the event and a copy here would
    #: be one two readers could disagree about — but this is ``opened_at``'s
    #: shape exactly, folded off one event's ``occurred_at`` and stored nowhere,
    #: so there is no second copy and nothing to disagree. What made the bare
    #: ``bool`` cost something is that ``updated_at`` is not the withdrawal: a
    #: withdraw is admitted while seats are still awaiting an answer, one of
    #: which may already have run out unanswered and unswept, so a sweep may
    #: append a ``SeatLapsed`` **after** the act. Dating the ending from the
    #: stream's last event would have moved a client's shelf life when a loop
    #: ran, which is the one thing that loop must never do.
    withdrawn_at: Instant | None = None
    #: Whether this court's line-up has ever completed into a game. **The second
    #: thing about a challenge that is not in its seats** (``docs/adr/0162``
    #: §2), folded off the acceptance that completed the line-up — the instant
    #: the hand-over opens the game — and off the mint of a mutual-born singles,
    #: which is complete at birth (``docs/adr/0165`` §2). It used to be folded
    #: off ``SeatLeft``, on the argument that a departure could only be written
    #: on a court that was ``ON``; a yes can be taken back before the court is
    #: whole now, so ``SeatLeft`` says somebody left and nothing more. Read by
    #: the fold so that a court one person is alone on is a game with a seat to
    #: fill rather than a send nobody answered. Off the seats it would be lost
    #: the moment a re-seat gave the departed's position to somebody else.
    game_opened: bool = False
    #: When each person who left this court did so, folded off ``SeatLeft`` and
    #: stored nowhere else — ``withdrawn_at``'s shape, for its reason
    #: ([#388](https://github.com/Raketa02/Raketa/issues/388)): a departure can
    #: end a court that has not been a game (``docs/adr/0165`` §3), and the
    #: ending's instant must not move when a sweep appends a lapse afterwards.
    #: A seat holds no instant for it — the deadline on a ``LEFT`` seat was met,
    #: not missed — so this is where the fold reads it. Keyed by player because
    #: nobody is asked twice on one challenge, so nobody leaves it twice.
    departed_at: Mapping[UUID, Instant] = field(default_factory=dict)
    version: int = 0
    _events: EventRecorder = field(
        default_factory=EventRecorder, init=False, repr=False, compare=False
    )

    @property
    def id(self) -> UUID:
        """The stream id. **Minted, and carried on the opening event.**

        There is nothing to derive it from that would still be true tomorrow: the
        people are the thing most likely to change, and two challenges between
        the same people are two challenges.
        """

        return self.challenge_id

    def pull_events(self) -> list[DomainEvent]:
        return self._events.pull()

    # -- opening ----------------------------------------------------------

    @classmethod
    def sent(
        cls,
        *,
        challenge_id: UUID,
        sport: Sport,
        mode: SearchMode | None,
        window: Window,
        organiser_id: UUID,
        arrangement: Sequence[SeatPlan],
        occurred_at: Instant,
    ) -> "Challenge":
        """Open a challenge from a court the organiser built.

        The organiser's seat is **accepted from birth**, because they are the one
        proposing — that is what makes *every seat accepted* the whole of the
        completion rule, with no special case for singles. Every other occupied
        seat is invited now and dated now; empty seats stay empty, and the
        challenge is half a game until somebody fills them.
        """

        _refuse_a_court_that_is_not(sport, [plan.side for plan in arrangement])
        _refuse_a_bad_line_up(arrangement, organiser_id=organiser_id)

        deadline = answer_by(occurred_at)
        seats = tuple(
            _seat_from(plan, organiser_id=organiser_id, deadline=deadline)
            for plan in arrangement
        )
        challenge = cls._empty()
        challenge._record_that(
            ChallengeSent(
                challenge_id=challenge_id,
                sport=sport.value,
                mode=None if mode is None else mode.value,
                window=window.value,
                organiser_id=organiser_id,
                seats=tuple(seat.code for seat in seats),
                occurred_at=occurred_at,
            )
        )
        return challenge

    @classmethod
    def opened_from_mutual_interest(
        cls,
        *,
        challenge_id: UUID,
        sport: Sport,
        mode: SearchMode | None,
        organiser_id: UUID,
        other_player_id: UUID,
        occurred_at: Instant,
    ) -> "Challenge":
        """Open a challenge from two yeses that met. **Both seats accepted.**

        No deadline, because nothing is owed: each of them has already said yes to
        the other, and asking either to answer again would make *you now have an
        open game together* not yet true. The pair take the court's first two
        positions — one per side in a singles sport, both on one side in a
        doubles one, which is a whole side still to fill.

        **The mode is a friendly or nothing, and the caller resolves it**
        (``docs/adr/0169`` §8): ``FOR_FUN`` when either of the pair declared
        *for fun* for this sport, ``None`` otherwise — which the hand-over
        reads as counted, *a friendly is a thing people choose*. It is required
        rather than defaulted so that the one place the rule is decided is the
        mint that reads the declarations, and not a constructor that decided it
        by omission. ``COMPETITIVE`` is refused as a broken precondition: it is
        not one of the rule's two outcomes, and stamping it would give two
        competitive declarers a mode where the rule gives them an absence.

        **The one-open-challenge-per-pair rule is the caller's here**, not this
        constructor's: it is a statement about every other challenge, and the
        path that detects a mutual is the one holding the read.
        """

        if organiser_id == other_player_id:
            raise CannotChallengeYourself()
        invariant(
            mode is not SearchMode.COMPETITIVE,
            "a mutual-born challenge is a friendly or nothing, never competitive",
        )

        sides = court_sides(sport)
        seats = tuple(
            Seat(
                side=side,
                player_id=player_id,
                answer=None if player_id is None else SeatAnswer.ACCEPTED,
            )
            for side, player_id in zip(
                sides,
                (organiser_id, other_player_id) + (None,) * (len(sides) - 2),
                strict=True,
            )
        )
        challenge = cls._empty()
        challenge._record_that(
            ChallengeOpenedFromMutualInterest(
                challenge_id=challenge_id,
                sport=sport.value,
                mode=None if mode is None else mode.value,
                organiser_id=organiser_id,
                other_player_id=other_player_id,
                seats=tuple(seat.code for seat in seats),
                occurred_at=occurred_at,
            )
        )
        return challenge

    # -- answering --------------------------------------------------------

    def accept(self, player_id: UUID, *, occurred_at: Instant) -> None:
        """One person says yes. **It matters on its own.**"""

        self._answerable_seat(player_id, now=occurred_at)
        self._record_that(
            SeatAccepted(
                challenge_id=self.challenge_id,
                player_id=player_id,
                occurred_at=occurred_at,
            )
        )

    def decline(self, player_id: UUID, *, occurred_at: Instant) -> None:
        """One person says no. It reopens **their** seat and nothing else."""

        self._answerable_seat(player_id, now=occurred_at)
        self._record_that(
            SeatDeclined(
                challenge_id=self.challenge_id,
                player_id=player_id,
                occurred_at=occurred_at,
            )
        )

    def leave(self, player_id: UUID, *, occurred_at: Instant) -> None:
        """One person leaves a court they had agreed to. It reopens **their** seat.

        **Any court that still stands** (``docs/adr/0165`` §1): a game
        (``docs/adr/0162``), a court reopened since and not yet re-seated, and
        — new — a court that has never been a game, whole or not. ``0162`` §1
        held that leaving a half-built court was a decline already given; it is
        given to an invitee who has not answered, and was not given to one who
        had. An ended challenge has nobody to leave, and the standing is asked
        before the seat so that somebody on an ended court is told that rather
        than told about their seat.

        **An accepted seat, and nobody else's.** The seat must be this player's
        and must hold their yes: a seat that is awaiting, declined, lapsed or
        already left has nothing to leave. The use case refuses those as it
        refuses a stranger, and this is the aggregate's backstop.

        What it does not ask is whether the game's moment has passed, because
        that is a fact about a **plan**, which this context cannot read. The use
        case asks the game, through a port, before it gets here — and only
        where there is a game; a half-built court has no moment to guard.

        What the fold makes of the departure is the fold's: before a game, one
        person left alone with nobody deciding is ``DECLINED``; on a game the
        court stands ``LINE_UP_INCOMPLETE`` and :meth:`is_deserted_at` is what
        the use case asks to call the game off.
        """

        if self.standing_at(occurred_at) in ENDED:
            raise TheChallengeIsOver()
        seat = self.seat_of(player_id)
        if seat is None or not seat.is_accepted():
            raise NotYourSeat()
        self._record_that(
            SeatLeft(
                challenge_id=self.challenge_id,
                player_id=player_id,
                occurred_at=occurred_at,
            )
        )

    def lapse(self, *, now: Instant) -> int:
        """Record every seat whose window has passed with nothing in it.

        **Idempotent by the aggregate, not by a lock**: a seat that already has
        an answer is skipped, so a second sweep over the same challenge appends
        nothing. Running it changes no read — the seats already read as lapsed —
        which is exactly why it can be a loop nobody has to trust.

        It answers with **how many seats it wrote down**, which is the one thing
        about a sweep that cannot be recovered afterwards: the seats read the
        same either side of it, so a caller that wanted the figure by comparing
        before and after would find nothing to compare. Zero is the ordinary
        answer and means the challenge had nothing owing — the sweep's read names
        candidates, not conclusions.

        **A day the organiser's removal cut short is not silence, and is not
        recorded** (``docs/adr/0142`` §5, the write side). A removed challenge
        holds seats whose day was still running when it was removed
        (``docs/adr/0165`` §4); their day passes on the clock all the same, and
        the seat reads as lapsed to anything that asks it — nothing downstream
        of an ended challenge does — but the record this sweep writes is the
        denominator *answers challenges* counts, and an invitation nobody was
        waiting on any more does not belong in it. A day that had **already**
        run out when the challenge was removed was silence, and is recorded as
        before; the history walk in ``event_sourced_challenge_history.py``
        draws the same line, seat by seat, and the two must not disagree.
        """

        recorded = 0
        for seat in self.seats:
            if seat.player_id is None or not seat.is_awaiting():
                continue
            if not seat.is_lapsed_at(now):
                continue
            if self.withdrawn_at is not None and not seat.is_lapsed_at(
                self.withdrawn_at
            ):
                continue
            self._record_that(
                SeatLapsed(
                    challenge_id=self.challenge_id,
                    player_id=seat.player_id,
                    occurred_at=now,
                )
            )
            recorded += 1
        return recorded

    # -- ending it ---------------------------------------------------------

    def withdraw(self, player_id: UUID, *, occurred_at: Instant) -> None:
        """*Remove the challenge* — or, on a court that has been a game, *call it
        off*. One event, two acts, and which one this is turns on
        :meth:`has_become_a_game` (``docs/adr/0165`` §4–§5).

        **Whole-challenge, and irreversible** (``docs/adr/0142`` §2). Per-seat
        would be the organiser removing an accepted player, which
        ``AnAcceptedPlayerMayNotBeRemoved`` refuses and keeps refusing — the
        people who already agreed did nothing wrong. A withdrawn challenge does
        not come back: re-asking the same people is a **new** challenge, with
        fresh deadlines and its own ``answered`` set, which is what it actually
        is. The seats are left exactly as they were, whatever they hold.

        **On a court that was never a game, the organiser removes it, and only
        while nobody else has joined.** Admitted exactly while nobody besides the
        organiser holds an accepted seat — before anybody has answered, and
        again once everybody who joined has left — whatever seats are still
        awaiting an answer; refused the moment one person is in, because a
        court somebody has joined is nobody's to end for the others. From then
        on the organiser leaves like anybody else (``leave``), and the court is
        over by itself when at most one player is on it and nobody is still
        deciding (``docs/adr/0165`` §3). ``docs/adr/0142`` §2 refused the
        pre-answer case so that a withdraw-and-resend could not hand the same
        person a fresh clock; ``0165`` §4 overrules that on the simplicity rule
        and names the falsifier, and ``NobodyIsAskedTwice`` is still scoped to
        one aggregate.

        **On a court that has been a game, any player on it calls the game off,
        while a seat is open.** ``LINE_UP_INCOMPLETE`` and nowhere else
        (``docs/adr/0163`` §2): a whole court has no seat to call it off for, and
        one whose open seat a newcomer is deciding on is not half built yet. The
        game is called off in the same transaction, one layer up, and the room
        is destroyed as it is for any withdrawal; ``game_opened`` stays true.
        The organiser's seat buys nothing here — ``0163`` §1's organiser-first
        rule and its fallback are gone (``0165`` §5).

        **Whose act it is, asked first, and it reads no standing.** The caller
        holds an **accepted** seat — the organiser's is accepted from birth, and
        one they left is not on the court — and on a court that was never a
        game they are the organiser. That the caller may not end this court is
        true regardless of what the fold says, exactly as *who is on the court*
        is checked ahead of anything a send has to read; asking the standing
        first would tell an invitee which standings they cannot end, one probe
        at a time. **Then whether it has ended**, with the word every other act
        here uses for one, and only then the act's own question.
        """

        if not self._holds_the_exit(player_id):
            raise TheWithdrawIsTheOrganisers()
        standing = self.standing_at(occurred_at)
        if standing in ENDED:
            raise TheChallengeIsOver()
        if self.has_become_a_game():
            if standing is not Standing.LINE_UP_INCOMPLETE:
                raise OnlyAHalfBuiltLineUpIsWithdrawn()
        elif self._somebody_has_joined():
            raise SomebodyHasJoinedTheCourt()
        self._record_that(
            ChallengeWithdrawn(
                challenge_id=self.challenge_id, occurred_at=occurred_at
            )
        )

    def _holds_the_exit(self, player_id: UUID) -> bool:
        """Whether this player may withdraw: they are on the court — an accepted
        seat, which a departure takes away and nothing gives back — and, on a
        court that was never a game, they are the organiser.

        **No clock**, because neither fact reads one: an acceptance is an
        answer on the seat, and whether the court has been a game is folded off
        the completion (``docs/adr/0165`` §2). A seat still awaiting an answer
        is live but not *on the court*, which is why a newcomer deciding on a
        fill cannot call the game off — they have not joined it yet.
        """

        seat = self.seat_of(player_id)
        if seat is None or not seat.is_accepted():
            return False
        return self.has_become_a_game() or player_id == self.organiser_id

    def _somebody_has_joined(self) -> bool:
        """Whether anybody besides the organiser holds an accepted seat.

        The seats and never the standing (``docs/adr/0165`` §4): a court that
        was never a game is ``LINE_UP_INCOMPLETE`` only because somebody joined
        it, and ``AWAITING_ANSWERS`` with one yes on it is a court somebody has
        joined too. A seat that was accepted and then left is not one — the
        departure wrote ``LEFT`` over the yes — which is what admits the
        organiser again once everybody who joined has gone.
        """

        return any(
            seat.is_accepted() and seat.player_id != self.organiser_id
            for seat in self.seats
        )

    # -- completing a half-built game -------------------------------------

    def invite(
        self,
        arrangement: Sequence[SeatPlan],
        *,
        by: UUID,
        occurred_at: Instant,
    ) -> None:
        """Fill the open seats, and arrange the court that results.

        **Only the newly seated are invited.** Everybody already in keeps their
        answer and their own deadline; they may be moved across the net, and they
        may not be taken out. A send with nobody new is **refused rather than
        recorded**, which is where *once the court is full, the sides are frozen*
        comes from: the only door back into an arrangement is an open seat.

        ``by`` is the member who filled them, recorded because *any live member
        may fill* — so the person who asked is a fact nothing else on the stream
        holds.
        """

        if self.standing_at(occurred_at) in ENDED:
            raise TheChallengeIsOver()
        still_in = {
            seat.player_id: seat
            for seat in self.seats
            if seat.is_live_at(occurred_at) and seat.player_id is not None
        }
        _refuse_a_court_that_is_not(self.sport, [plan.side for plan in arrangement])
        _refuse_a_bad_line_up(
            arrangement, organiser_id=self.organiser_seat_required(occurred_at)
        )

        planned = {plan.player_id for plan in arrangement if plan.player_id}
        if not set(still_in) <= planned:
            raise AnAcceptedPlayerMayNotBeRemoved()

        newly_invited = tuple(
            plan.player_id
            for plan in arrangement
            if plan.player_id is not None and plan.player_id not in still_in
        )
        if not newly_invited:
            raise NobodyNewToInvite()
        if self.already_asked_at(occurred_at) & set(newly_invited):
            raise NobodyIsAskedTwice()

        deadline = answer_by(occurred_at)
        seats = tuple(
            _still_in(still_in[plan.player_id], plan)
            if plan.player_id in still_in
            else _seat_from(plan, organiser_id=self.organiser_id, deadline=deadline)
            for plan in arrangement
        )
        self._record_that(
            SeatsInvited(
                challenge_id=self.challenge_id,
                seats=tuple(seat.code for seat in seats),
                newly_invited=tuple(str(player_id) for player_id in newly_invited),
                occurred_at=occurred_at,
                invited_by=by,
            )
        )

    # -- reading ----------------------------------------------------------

    def standing_at(self, now: Instant) -> Standing:
        """What this challenge is, right now. **Derived, never stored.**"""

        return standing_of(
            self.seats,
            now=now,
            withdrawn=self.withdrawn_at is not None,
            game_opened=self.game_opened,
        )

    def ended_at(self, now: Instant) -> Instant | None:
        """When it ended, or ``None`` because it has not. **Derived too.**

        The same fold's other half, and it takes the same ``now`` so that a
        caller with one reading of the clock cannot get a standing from one
        instant and an ending from another.

        **Three of the four endings are exact and the decline is an upper
        bound**, which ``standing.py`` explains and the wire repeats — a field
        documented as an instant while serving a bound is how a later reader
        invents exactness that was never there.
        """

        return ended_at_of(
            self.seats,
            now=now,
            updated_at=self.updated_at,
            withdrawn_at=self.withdrawn_at,
            game_opened=self.game_opened,
            departed_at=self.departed_at,
        )

    def organiser_seat_required(self, now: Instant) -> UUID | None:
        """Whose seat a court posted to this challenge must hold, or nobody's.

        The organiser holds a seat because *they are the one proposing*, and a
        court that dropped them would be a court proposed by nobody. Once they
        have **left** (``docs/adr/0162`` §2) that is exactly what the court is:
        filled by whoever is still on it, with the organiser in ``answered`` and
        never asked again. So the rule is asked only while they are live — which
        *everybody live keeps their seat* already covers — and ``None`` here
        tells the court check to ask nothing about them.
        """

        organiser = self.seat_of(self.organiser_id)
        if organiser is not None and organiser.is_live_at(now):
            return self.organiser_id
        return None

    def has_become_a_game(self) -> bool:
        """Whether this challenge's line-up completed and handed over a game.

        ``ON``, or a court that has been ``ON`` and lost somebody since
        (``docs/adr/0162``) — which is *every seat accepted*, the moment the
        hand-over fires, and the game it opened stands whether or not a seat has
        since reopened. A singles challenge born of two yeses is ``ON`` the
        instant it exists and no accept ever happens on it. **It takes no
        clock** (``docs/adr/0165`` §2): the fact is folded off the completion
        itself and nothing about the passing of time can make or unmake it.

        **It is one end of the mutual mint's idempotence key** (``docs/adr/0152``
        §4): *has a mutual between these two already minted a game in this sport,
        and is that game finished with?* This half is answerable here; the other
        half is a fact about a **game**, which this context does not own, and it
        is asked through ``SettledGameQuery``.

        There is no complement to this and there is deliberately no *has it
        ended* beside it. A challenge that ended without ever reaching ``ON``
        minted nothing, so it holds nobody — and a predicate saying *this
        challenge still stands* is the subtly-wrong second answer to *are these
        two arranging something* that the pair rule already answers.
        """

        return self.game_opened

    def is_deserted_at(self, now: Instant) -> bool:
        """Whether at most one player is on this court and nobody is deciding —
        **the ending rule** (``docs/adr/0165`` §3), asked of a court that has
        been a game.

        Before a game the fold reads the same rule and the answer is a standing;
        on a game the fold does not end the court (``docs/adr/0162`` §2), and
        this is how the departure asks it after recording itself, to hand
        ``call_off`` to ``games`` in the same transaction. The rule is written
        once, in ``standing.py``, so the two readers cannot come to two answers
        about one court.
        """

        return deserted(self.seats, now=now)

    def is_being_arranged_at(self, now: Instant) -> bool:
        """Whether these people are **still arranging a game** — the pair rule.

        Not *has it ended*, and deliberately not its complement (``docs/adr/0142``
        §1). A challenge whose line-up completed is ``ON``: it has not ended —
        ``invite`` does not call it over and the client still prints ``ON`` —
        but the arranging is over, a game exists, and there is nothing left for
        the rule to hold two people apart for.
        """

        return self.standing_at(now) in ARRANGING

    def already_asked_at(self, now: Instant) -> frozenset[UUID]:
        """Everybody this challenge has put a question to and had closed.

        **``answered`` plus the clock, and the clock half is the load-bearing
        one.** ``answered`` is folded off the answer events, so a seat whose day
        ran out is in it only once the sweep has appended a ``SeatLapsed`` — and
        the sweep exists *for the record, not for correctness*. Reading the set
        alone would make *may this person be asked again* depend on whether a
        loop had been past, which is the one thing this whole context refuses:
        a challenge reads the same at every instant either side of a sweep.

        So it is derived here, once, and both readers take it: ``invite``'s
        ``NobodyIsAskedTwice``, and the fill that keeps that refusal a backstop
        by leaving these people out of its pool (``docs/adr/0150`` §4). Two
        derivations would be two answers to *have they already been asked*, and
        the one that drifted would be the one that let somebody be asked twice.

        **It contains the people who accepted**, who are also still in the game —
        both readers subtract who is live, and neither wants a second rule about
        it here.
        """

        return self.answered | frozenset(
            seat.player_id
            for seat in self.seats
            if seat.player_id is not None and seat.is_lapsed_at(now)
        )

    def seat_of(self, player_id: UUID) -> Seat | None:
        """That player's seat on this court, or nothing if it is not theirs.

        ``None`` covers both *they were never here* and *their position was
        re-offered to somebody else*, and it does so on purpose: a seat that has
        moved on is not this person's to be asked about, which is the same rule
        the directory drops a stream on.
        """

        for seat in self.seats:
            if seat.holds(player_id):
                return seat
        return None

    def players_in_it_at(self, now: Instant) -> frozenset[UUID]:
        """Everybody still arranging this game: accepted, or yet to answer.

        **Sharing a line-up makes a pair.** Every occupied seat but your own is
        somebody you have an open game with — co-invitees and organiser alike —
        and a seat that declined or lapsed is empty again, so that person is a
        stranger to you once more the moment they leave.

        **And so is everybody, the moment the line-up completes.** A challenge
        that reached ``ON`` holds nobody: the pair rule exists to stop one game
        being arranged twice, and this one is arranged. Whether the *unplayed
        game* should carry a block of its own was filed here and is now
        **decided**: ``docs/adr/0152`` built the port onto ``games`` that would
        answer it and declined to use it on this read, because a send is somebody
        deliberately choosing a court. Nothing replaces the release, and that is
        the decision rather than the deferral.

        **And held again the moment somebody leaves** (``docs/adr/0162``): a
        reopened court is ``LINE_UP_INCOMPLETE``, its people are arranging once
        more, and the one who left is a stranger to them as a decliner is.
        """

        if not self.is_being_arranged_at(now):
            return frozenset()
        return self._seated_at(now)

    def _seated_at(self, now: Instant) -> frozenset[UUID]:
        """Every occupied seat that has neither declined nor lapsed."""

        return frozenset(
            seat.player_id
            for seat in self.seats
            if seat.player_id is not None and seat.is_live_at(now)
        )

    # -- folding ----------------------------------------------------------

    @classmethod
    def from_history(cls, events: Iterable[DomainEvent]) -> "Challenge":
        challenge = cls._empty()
        for event in events:
            challenge._apply(event)
        return challenge

    @classmethod
    def _empty(cls) -> "Challenge":
        challenge = cls.__new__(cls)
        challenge.version = 0
        challenge.seats = ()
        challenge.answered = frozenset()
        challenge.withdrawn_at = None
        challenge.game_opened = False
        challenge.departed_at = {}
        challenge._events = EventRecorder()
        return challenge

    def _record_that(self, event: DomainEvent) -> None:
        self._apply(event)
        self._events.record(event)

    def _apply(self, event: DomainEvent) -> None:
        if isinstance(event, ChallengeSent):
            self.challenge_id = event.challenge_id
            self.sport = Sport(event.sport)
            self.mode = None if event.mode is None else SearchMode(event.mode)
            self.window = Window(event.window)
            self.organiser_id = event.organiser_id
            self.seats = tuple(Seat.from_code(code) for code in event.seats)
            self.opened_at = instant(event.occurred_at)
            self._touch(event.occurred_at)
            return
        if isinstance(event, ChallengeOpenedFromMutualInterest):
            self.challenge_id = event.challenge_id
            self.sport = Sport(event.sport)
            self.mode = None if event.mode is None else SearchMode(event.mode)
            self.window = None
            self.organiser_id = event.organiser_id
            self.seats = tuple(Seat.from_code(code) for code in event.seats)
            self.opened_at = instant(event.occurred_at)
            # A mutual-born singles is complete at birth, and a game from it.
            self._note_a_completed_line_up()
            self._touch(event.occurred_at)
            return
        if isinstance(event, SeatAccepted):
            self._answer(event.player_id, SeatAnswer.ACCEPTED)
            # The acceptance that fills the last seat is the instant the
            # hand-over opens the game (``docs/adr/0165`` §2).
            self._note_a_completed_line_up()
            self._touch(event.occurred_at)
            return
        if isinstance(event, SeatDeclined):
            self._answer(event.player_id, SeatAnswer.DECLINED)
            self._touch(event.occurred_at)
            return
        if isinstance(event, SeatLapsed):
            self._answer(event.player_id, SeatAnswer.LAPSED)
            self._touch(event.occurred_at)
            return
        if isinstance(event, SeatLeft):
            # Somebody left, and that is all the fold learns from it: whether
            # this court had become a game was noted at the completion.
            self._answer(event.player_id, SeatAnswer.LEFT)
            self.departed_at = {
                **self.departed_at,
                event.player_id: instant(event.occurred_at),
            }
            self._touch(event.occurred_at)
            return
        if isinstance(event, SeatsInvited):
            self.seats = tuple(Seat.from_code(code) for code in event.seats)
            self._touch(event.occurred_at)
            return
        if isinstance(event, ChallengeWithdrawn):
            # The seats are left exactly as they were, which is the point: the
            # person who accepted still accepted, and a withdraw that emptied
            # their seat would be the organiser removing them.
            self.withdrawn_at = instant(event.occurred_at)
            self._touch(event.occurred_at)
            return
        raise TypeError(f"Unsupported challenge event {event!r}")

    def _answer(self, player_id: UUID, answer: SeatAnswer) -> None:
        self.seats = tuple(
            seat.answered(answer) if seat.holds(player_id) else seat
            for seat in self.seats
        )
        self.answered |= {player_id}

    def _note_a_completed_line_up(self) -> None:
        """Every seat accepted: the line-up has completed, and a game is opened
        from it in the same transaction. Once true it stays true — a departure
        opens a seat on that game rather than un-opening it."""

        if all(seat.is_accepted() for seat in self.seats):
            self.game_opened = True

    def _touch(self, occurred_at: datetime) -> None:
        self.updated_at = instant(occurred_at)
        self.version += 1

    def _answerable_seat(self, player_id: UUID, *, now: Instant) -> Seat:
        """The seat this player may answer for, or the reason they may not."""

        for seat in self.seats:
            if not seat.holds(player_id):
                continue
            # **The window is asked about first, and the order is the rule.** A
            # seat past its deadline reads as lapsed whether or not the sweep has
            # been past, so testing the recorded answer first would answer *you
            # already answered* after a sweep and *your window has passed* before
            # one — the same act refused with two codes depending on whether a
            # loop happened to run.
            if seat.is_lapsed_at(now):
                raise TheAnswerWindowHasPassed()
            if seat.answer is not None:
                raise TheSeatIsAlreadyAnswered()
            # **The challenge last, and only one ending can reach it.** A seat
            # still inside its window with no answer on it is a seat somebody is
            # deciding on, and a court with one of those is not deserted — so the
            # only ended challenge it can sit on is one its organiser removed
            # (``docs/adr/0165`` §4). The seat's own facts come first for the
            # reason above: a late answer is told its window passed whether or
            # not the other seats happened to lapse the court with it.
            if self.standing_at(now) in ENDED:
                raise TheChallengeIsOver()
            return seat
        raise NotYourSeat()


def _still_in(seat: Seat, plan: SeatPlan) -> Seat:
    """Somebody already in the game, on the side the new arrangement gives them.

    They keep their answer, their own deadline and the origin they were drawn
    from: **an acceptance is to the game, not to the side.** A plan that carries
    an origin for them is a caller that thinks it is inviting somebody it is not,
    and it raises rather than having the origin quietly dropped — a discarded
    origin is the silent half of *never an optional field*.
    """

    invariant(
        plan.origin is None,
        f"an invitation addressed to somebody already in the game: {plan!r}",
    )
    return seat.on_side(plan.side)


def _seat_from(plan: SeatPlan, *, organiser_id: UUID, deadline: Instant) -> Seat:
    """The seat a plan becomes: empty, the organiser's, or an invitation."""

    if plan.player_id is None:
        return Seat(side=plan.side)
    if plan.player_id == organiser_id:
        return Seat(side=plan.side, player_id=organiser_id, answer=SeatAnswer.ACCEPTED)
    invariant(
        plan.origin is not None,
        f"an invitation that cannot say where it came from: {plan!r}",
    )
    return Seat(
        side=plan.side,
        player_id=plan.player_id,
        answer_by=deadline,
        origin=plan.origin,
    )


def _refuse_a_court_that_is_not(sport: Sport, sides: Sequence[Side]) -> None:
    """The court is the sport's, in the sport's own order, or it is refused.

    Checked against the fixed list rather than counted, because *which side is
    short* is a fact this aggregate promises to hold and a court whose sides
    arrive in some caller's order could not answer it the same way twice.
    """

    expected = court_sides(sport)
    if tuple(sides) != expected:
        raise TheCourtIsNotThisSports(
            f"A {sport.value} court is "
            f"{''.join(side.value for side in expected)}, "
            f"not {''.join(side.value for side in sides)!r}."
        )


def refuse_a_bad_court(
    occupants: Sequence[UUID | None], *, organiser_id: UUID | None
) -> None:
    """The four things about *who is on the court* that are a caller's bug.

    ``organiser_id`` is ``None`` for a court proposed by nobody — one whose
    organiser has **left** the game it became (``docs/adr/0162`` §2) — and the
    two rules about them are then not asked; ``Challenge.organiser_seat_required``
    is where that is decided, so a caller never decides it for itself.

    **It takes the occupants and not the arrangement, so that it needs no
    sport.** A send has to be able to refuse *nobody to invite* before it has
    read anything at all — the refusal is a fact about the send's shape and is
    true regardless of anybody else's state, and telling an organiser their
    line-up went stale when they invited nobody sends them refreshing a screen
    that was never wrong. The court's *shape* is the one refusal in this family
    that cannot go first: it is the sport's, and the sport is read off the search
    the court was built on.

    Public for that one caller. It is still run again by the aggregate, from
    :func:`_refuse_a_bad_line_up`, which is the point — the use case makes the
    **order** observable and this stays the only place the rule is written.
    """

    seated = [one for one in occupants if one is not None]
    if organiser_id is not None:
        if organiser_id not in seated:
            raise TheOrganiserHoldsASeat()
        if seated.count(organiser_id) > 1:
            raise CannotChallengeYourself()
    if len(set(seated)) != len(seated):
        raise OnePersonToASeat()
    if len(seated) < 2:
        raise AChallengeNeedsAnInvitee()


def _refuse_a_bad_line_up(
    arrangement: Sequence[SeatPlan], *, organiser_id: UUID | None
) -> None:
    """The same four, plus the one that is about the arrangement rather than the
    people: an organiser cannot arrive carrying an invitation to themselves."""

    refuse_a_bad_court(
        [plan.player_id for plan in arrangement], organiser_id=organiser_id
    )
    if organiser_id is not None and any(
        plan.player_id == organiser_id and plan.origin is not None
        for plan in arrangement
    ):
        raise CannotChallengeYourself()
