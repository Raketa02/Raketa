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
new to invite, and a withdraw that is not the organiser's or is asked of a
standing that has some other end already. Everything else this context knows is
derived.

**One act here announces its own conclusion, and exactly one may**
(``docs/adr/0142``). ``withdraw`` records the only standing no arrangement of the
seats could reach; every other transition changes a seat and lets the fold
answer.

**What it does not refuse, and states as an invariant instead:** *an acceptance
is to the game, not to the side.* The membership is settled; the arrangement is
still the organiser's to choose, and ``invite`` is written to let exactly that
happen.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable, Sequence
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
    #: from a surface with no mode — the deck — and on every mutual-born
    #: challenge, where nobody picked one.
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
    #: Whether the organiser has ended it. **The one thing about a challenge that
    #: is not in its seats** — a decision somebody took, folded off
    #: ``ChallengeWithdrawn`` and read by ``standing_at`` before anything else.
    #: A ``bool`` and not an instant, because it is folded exactly as an answer
    #: is: the moment it happened is the event's, and a second copy on the
    #: aggregate would be a moment two readers could disagree about.
    withdrawn: bool = False
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

        **The one-open-challenge-per-pair rule is the caller's here**, not this
        constructor's: it is a statement about every other challenge, and the
        path that detects a mutual is the one holding the read. Nothing in this
        module calls this yet, and the ticket that wires it signs for that check.
        """

        if organiser_id == other_player_id:
            raise CannotChallengeYourself()

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
        """

        recorded = 0
        for seat in self.seats:
            if seat.player_id is None or not seat.is_awaiting():
                continue
            if not seat.is_lapsed_at(now):
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
        """The organiser ends a line-up nobody is going to complete.

        **Whole-challenge, and irreversible** (``docs/adr/0142`` §2). Per-seat
        would be the organiser removing an accepted player, which
        ``AnAcceptedPlayerMayNotBeRemoved`` refuses and keeps refusing — the
        people who already agreed did nothing wrong. A withdrawn challenge does
        not come back: re-asking the same people is a **new** challenge, with
        fresh deadlines and its own ``answered`` set, which is what it actually
        is.

        **``LINE_UP_INCOMPLETE`` and nowhere else**, because the rule is *the
        exit exists exactly where nothing else ends it*. ``AWAITING_ANSWERS``
        ends itself when the clocks run out, and the only thing a withdraw would
        add there is the ability to ask the same person again tomorrow —
        ``NobodyIsAskedTwice`` is scoped to one aggregate and cannot see a
        withdraw-and-resend. ``ON`` has become a game and ending the challenge
        would not touch it.

        **Whose act it is, asked first.** That the caller is not the organiser is
        true regardless of what the seats say, exactly as *who is on the court*
        is checked ahead of anything a send has to read; asking the standing
        first would tell an invitee which standings they cannot end, one probe at
        a time.
        """

        if player_id != self.organiser_id:
            raise TheWithdrawIsTheOrganisers()
        if self.standing_at(occurred_at) is not Standing.LINE_UP_INCOMPLETE:
            raise OnlyAHalfBuiltLineUpIsWithdrawn()
        self._record_that(
            ChallengeWithdrawn(
                challenge_id=self.challenge_id, occurred_at=occurred_at
            )
        )

    # -- completing a half-built game -------------------------------------

    def invite(self, arrangement: Sequence[SeatPlan], *, occurred_at: Instant) -> None:
        """Fill the open seats, and arrange the court that results.

        **Only the newly seated are invited.** Everybody already in keeps their
        answer and their own deadline; they may be moved across the net, and they
        may not be taken out. A send with nobody new is **refused rather than
        recorded**, which is where *once the court is full, the sides are frozen*
        comes from: the only door back into an arrangement is an open seat.
        """

        if self.standing_at(occurred_at) in ENDED:
            raise TheChallengeIsOver()
        _refuse_a_court_that_is_not(self.sport, [plan.side for plan in arrangement])
        _refuse_a_bad_line_up(arrangement, organiser_id=self.organiser_id)

        still_in = {
            seat.player_id: seat
            for seat in self.seats
            if seat.is_live_at(occurred_at) and seat.player_id is not None
        }
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
        if self.answered & set(newly_invited):
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
            )
        )

    # -- reading ----------------------------------------------------------

    def standing_at(self, now: Instant) -> Standing:
        """What this challenge is, right now. **Derived, never stored.**"""

        return standing_of(
            self.seats,
            organiser_id=self.organiser_id,
            now=now,
            withdrawn=self.withdrawn,
        )

    def has_become_a_game_at(self, now: Instant) -> bool:
        """Whether this challenge's line-up completed and handed over a game.

        ``ON`` and nothing else, which is *every seat accepted* — the moment
        ``PlannedGameOpening`` fires and the only moment it can, because after it
        the membership may not change. A singles challenge born of two yeses is
        ``ON`` the instant it exists and no accept ever happens on it.

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

        return self.standing_at(now) is Standing.ON

    def is_being_arranged_at(self, now: Instant) -> bool:
        """Whether these people are **still arranging a game** — the pair rule.

        Not *has it ended*, and deliberately not its complement (``docs/adr/0142``
        §1). A challenge whose line-up completed is ``ON``: it has not ended —
        ``invite`` does not call it over and the client still prints ``ON`` —
        but the arranging is over, a game exists, and there is nothing left for
        the rule to hold two people apart for.
        """

        return self.standing_at(now) in ARRANGING

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
        challenge.withdrawn = False
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
            self.mode = None
            self.window = None
            self.organiser_id = event.organiser_id
            self.seats = tuple(Seat.from_code(code) for code in event.seats)
            self.opened_at = instant(event.occurred_at)
            self._touch(event.occurred_at)
            return
        if isinstance(event, SeatAccepted):
            self._answer(event.player_id, SeatAnswer.ACCEPTED)
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
        if isinstance(event, SeatsInvited):
            self.seats = tuple(Seat.from_code(code) for code in event.seats)
            self._touch(event.occurred_at)
            return
        if isinstance(event, ChallengeWithdrawn):
            # The seats are left exactly as they were, which is the point: the
            # person who accepted still accepted, and a withdraw that emptied
            # their seat would be the organiser removing them.
            self.withdrawn = True
            self._touch(event.occurred_at)
            return
        raise TypeError(f"Unsupported challenge event {event!r}")

    def _answer(self, player_id: UUID, answer: SeatAnswer) -> None:
        self.seats = tuple(
            seat.answered(answer) if seat.holds(player_id) else seat
            for seat in self.seats
        )
        self.answered |= {player_id}

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
    occupants: Sequence[UUID | None], *, organiser_id: UUID
) -> None:
    """The four things about *who is on the court* that are a caller's bug.

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
    if organiser_id not in seated:
        raise TheOrganiserHoldsASeat()
    if seated.count(organiser_id) > 1:
        raise CannotChallengeYourself()
    if len(set(seated)) != len(seated):
        raise OnePersonToASeat()
    if len(seated) < 2:
        raise AChallengeNeedsAnInvitee()


def _refuse_a_bad_line_up(
    arrangement: Sequence[SeatPlan], *, organiser_id: UUID
) -> None:
    """The same four, plus the one that is about the arrangement rather than the
    people: an organiser cannot arrive carrying an invitation to themselves."""

    refuse_a_bad_court(
        [plan.player_id for plan in arrangement], organiser_id=organiser_id
    )
    if any(
        plan.player_id == organiser_id and plan.origin is not None
        for plan in arrangement
    ):
        raise CannotChallengeYourself()
