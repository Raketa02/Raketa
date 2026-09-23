"""The Plan aggregate — one court's three slots and its lock, event-sourced.

**Where and when these people are meeting.** It is *one challenge's*, identified
by that challenge's id (``docs/adr/0164`` §1), and it sits between the two
contexts either side of it: ``challenges`` ends at *everybody has answered* and
``games`` begins at *played*, and this belongs to neither (``docs/adr/0144``).
The game the challenge becomes inherits it.

Six things about it are load-bearing and none is obvious from the code alone.

**It is born by being used.** There is no opening event, no record at birth and
no subscriber to ``SeatAccepted`` or ``GamePlanned``: ``unwritten`` is what a
court with nothing agreed has, and it is a real state rather than a placeholder
— the write path starts from it, and so does the read, which answers a row for
every court the reader may plan whether or not anything was ever written
(``docs/adr/0164`` §4). A row of three empty slots **is** *nothing agreed*, and
it is one spelling: the store holds no stream, and the read spells that as an
unwritten plan rather than as an absence a client would have to tell apart from
a court it was not shown.

There is **no flag saying whether anything has been agreed**, and the reason is
that nothing would ask: the write path starts from an unwritten plan whatever it
holds, and the read folds the streams that exist and answers ``unwritten`` for
the rest. A property that only a test reads is a claim about a shape nothing
checks.

**Its id is the challenge's**, so there is one plan per challenge for ever. A
second id would be a second name for the same thing, and it would need a lookup
by payload to be found; keying on the challenge's id makes the stream read an
equality on the aggregate id and makes *one challenge, one plan* a fact about
the store rather than a rule a caller keeps. One challenge has at most one room
and at most one game, and both already carry ``challenge_id`` — it is the one id
every reader shares, which is why the room draws the plan from its opening and
the game finds it by the challenge it was opened from.

**Nothing derived is stored.** Not the slot count, not the agreed point. Both are
properties folded from the three values, and neither the anchor nor
``planned_at`` is ever written — the anchor arrives per write and is measured
against, ``planned_at`` keeps meaning *when it became a game*, and the plan
never writes to ``games`` at all.

**Any member may fill or change any slot, any number of times, and a slot is
never emptied.** There is no history beyond the system lines each change writes
and no rate limit — *the line is the friction*. Last write wins, so a plan can be
moved under somebody who has already read it, and that is accepted: the
alternative is a proposal each person accepts, which is the negotiation this card
exists not to be.

**The count and the lock are two facts, and locking freezes nothing**
(``docs/adr/0155``). ADR-0144 folded them together — *filling the third slot is
the lock* — and this aggregate now keeps them apart: ``slot_count == SLOTS`` says
a plan is one everybody *could* agree, and ``is_locked`` says somebody did. After
a lock any member may still move a slot, and each move writes its own line
exactly as it did before; there is no un-agreeing to fear, only re-agreeing
(``docs/adr/0145`` §5). There is no ``unlock``, for the same reason there is no
clearing event: the lock is a thing that happened.

**The lock waits for the court** (``docs/adr/0164`` §5). Where, day and hour
are proposals anybody on the court may make and move, whole or not; *we are
agreed* is said only once everybody who will have to keep it is in. Whether the
court is whole is a fact the aggregate **borrows**, exactly as ``record_day``
borrows the anchor, and refuses with a code of its own beside *the plan is not
complete*. A lock already taken survives the court ceasing to be whole: a
departure opens a seat and unmakes nothing.

**Who may write at all is not decided here.** *Is this player on this court,
and is that court still open to planning* is one question asked through one
port, and the two refusals it produces belong to the use case that asks it. What
this aggregate refuses is what it can see: the **values** — a day past the
horizon, an hour nobody offered, a moment that has gone — and, since
``docs/adr/0155``, **its own state**, because a lock is guarded on how far along
the plan is and nothing outside can answer that; and, since ``docs/adr/0164``,
the one fact about the court it is handed for the lock.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from datetime import time as wall_time
from typing import Iterable
from uuid import UUID

from app.kernel import Instant, MinuteOfDay, instant, minute_of_day
from app.modules.plans.domain.errors import (
    ThatMomentHasAlreadyPassed,
    TheCourtIsNotWhole,
    ThePlanIsNotComplete,
)
from app.modules.plans.domain.events import (
    DayRecorded,
    HourRecorded,
    PlaceRecorded,
    PlanLocked,
)
from app.modules.plans.domain.slots import (
    Place,
    agreed_point,
    hour_of,
    moment_of,
    refuse_a_day_past_the_horizon,
)
from app.shared.domain import DomainEvent
from app.shared.domain.events import EventRecorder

#: How many slots there are. Spelled once, and it says **how far along a plan
#: is** and nothing more: a plan with all three filled is one everybody *could*
#: agree, which is not the same fact as somebody having agreed it
#: (``docs/adr/0155``). It is what ``lock`` is guarded on and never what
#: ``is_locked`` reads.
SLOTS = 3


@dataclass
class Plan:
    """One challenge's plan, rebuilt by folding its stream."""

    challenge_id: UUID
    place: Place | None
    day: date | None
    hour: MinuteOfDay | None
    #: When somebody agreed the plan, or ``None`` while nobody has. **Folded,
    #: never a column** — like every other value here it is read off the stream,
    #: and it is the one thing on this aggregate that is not a slot.
    locked_at: Instant | None = None
    version: int = 0
    _events: EventRecorder = field(
        default_factory=EventRecorder, init=False, repr=False, compare=False
    )

    @property
    def id(self) -> UUID:
        """The stream id, which **is** the challenge's id."""

        return self.challenge_id

    @property
    def slot_count(self) -> int:
        """How many of the three are filled. **Derived, never stored.**

        The count three cards are keyed on (``docs/adr/0148``), and it lives here
        rather than in a column because a stored count is the copy that gets
        believed the first time it disagrees with the values beside it.
        """

        return sum(one is not None for one in (self.place, self.day, self.hour))

    @property
    def agreed_point(self) -> Instant | None:
        """The plan's moment, or ``None`` while no day is recorded.

        Derived and **sent** rather than derived and stored: it is a timezone
        conversion the client must not redo (``docs/adr/0148`` §8), and storing it
        would be a second place for one fact to be true — one that a day change
        could leave behind.
        """

        return agreed_point(day=self.day, hour=self.hour)

    @property
    def is_locked(self) -> bool:
        """Whether somebody has agreed this plan.

        **Explicitly not ``slot_count == SLOTS``**, and that distinction is the
        whole of ``docs/adr/0155``: a complete plan is one everybody *could*
        agree, and nobody has until somebody says so. Reading the count here
        would put ADR-0144's folded-together version of the two facts back, in
        the one property that would then be believed.
        """

        return self.locked_at is not None

    def pull_events(self) -> list[DomainEvent]:
        return self._events.pull()

    # -- birth ------------------------------------------------------------

    @classmethod
    def unwritten(cls, challenge_id: UUID) -> "Plan":
        """The plan a court with nothing agreed has.

        **Not a factory for an empty record**, because no record is written: it
        is the value the repository answers with when a stream is empty — and
        the row the list read answers for a court nobody has written on — and
        the first recording below is what brings it into existence.
        """

        return cls(challenge_id=challenge_id, place=None, day=None, hour=None)

    @classmethod
    def from_history(cls, events: Iterable[DomainEvent]) -> "Plan":
        """Rebuild from the stream. **Any of the four may be the first event.**

        There is no opening event to construct from, so the challenge id is read
        off whichever event happens to be first — every one of them carries it, and
        each of the three recordings can be a birth. A lock cannot be one, but it
        is read as though it could: the fold's job is to make a stream readable,
        not to re-decide what may be in it.
        """

        plan: Plan | None = None
        for event in events:
            if plan is None:
                plan = cls.unwritten(_challenge_of(event))
            plan._apply(event)
        if plan is None:
            raise ValueError("a plan cannot be folded from no events at all")
        return plan

    # -- the three recordings ---------------------------------------------

    def record_place(self, *, place: str, by: UUID, occurred_at: Instant) -> None:
        """*We are meeting here.* Setting and moving are one act.

        **Writing the value already there records nothing** (``docs/adr/0148``
        §8). Without that the room fills with *Tomek set the place* three times
        over, and it is this repository's own idempotency language: the same
        value twice lands the same state and records nothing the second time.

        The comparison is made **after** normalisation, so trailing whitespace is
        not a change and does not write a line.
        """

        written = Place.of(place)
        if written == self.place:
            return
        self._record_that(
            PlaceRecorded(
                challenge_id=self.challenge_id,
                place=written.value,
                recorded_by=by,
                occurred_at=occurred_at,
            )
        )

    def record_day(
        self, *, day: date, by: UUID, anchor: Instant, occurred_at: Instant
    ) -> None:
        """*We are playing on this day.*

        Two refusals, in this order and deliberately: **the clamp** first, because
        a day past the horizon is not a day this plan may hold at all; then **the
        past combination**, which only exists once an hour is already recorded.

        ``anchor`` is the court's and arrives from the caller — the challenge's
        send until the game exists, then the game's ``planned_at``
        (``docs/adr/0164`` §4). It is one of the two facts this aggregate
        borrows, and it is borrowed rather than stored because the plan never
        writes to ``challenges`` or ``games`` and must not hold a copy of
        anything they do.
        """

        if day == self.day:
            return
        refuse_a_day_past_the_horizon(day, anchor=anchor)
        self._refuse_a_moment_that_has_gone(day=day, hour=self.hour, now=occurred_at)
        self._record_that(
            DayRecorded(
                challenge_id=self.challenge_id,
                day=day.isoformat(),
                recorded_by=by,
                occurred_at=occurred_at,
            )
        )

    def record_hour(
        self, *, hour: wall_time, by: UUID, occurred_at: Instant
    ) -> None:
        """*We are playing at this time.*

        **No horizon applies to an hour**, and that is not an omission: the clamp
        is about which day a plan may name, and an hour on a plannable day is
        plannable by construction. What can still be refused is the pair, which is
        the same refusal ``record_day`` makes from the other side.
        """

        offered = hour_of(hour)
        if offered == self.hour:
            return
        self._refuse_a_moment_that_has_gone(
            day=self.day, hour=offered, now=occurred_at
        )
        self._record_that(
            HourRecorded(
                challenge_id=self.challenge_id,
                minute_of_day=int(offered),
                recorded_by=by,
                occurred_at=occurred_at,
            )
        )

    # -- the act ----------------------------------------------------------

    def lock(
        self, *, by: UUID, occurred_at: Instant, court_is_whole: bool
    ) -> None:
        """*We are agreed.* **An act with an actor and a moment.**

        ``docs/adr/0155``. It carries no value, because the value is the three
        slots and they are already recorded — a copy here would be the first
        thing to disagree with the slot beside it after a later move.

        **The three answers are deliberately different shapes.** A plan that is
        already locked records nothing: the same act twice lands the same state,
        which is this repository's idempotency language applied to an act rather
        than to a value, and the first lock's moment is the one that stands —
        **whatever the court has become since**, because a departure after the
        lock unmakes nothing (``docs/adr/0164`` §5). A court that is **not
        whole** raises, with its own code: *we are agreed* is said only once
        everybody who will have to keep it is in, and it is asked before the
        count because the count is a fact about a button the card does not draw
        until the court is whole. A plan that is **not complete** raises, because
        a silent no-op there would leave a client believing it had agreed one.

        ``court_is_whole`` is the second fact this aggregate borrows, on
        ``record_day``'s terms exactly: handed in per act, measured against, and
        stored nowhere.

        **It freezes nothing.** No slot write consults ``locked_at`` — not here
        and nowhere else — so a locked plan is edited exactly as an unlocked one
        is, and the room's line trail is the whole of the friction.
        """

        if self.is_locked:
            return
        if not court_is_whole:
            raise TheCourtIsNotWhole()
        if self.slot_count < SLOTS:
            raise ThePlanIsNotComplete()
        self._record_that(
            PlanLocked(
                challenge_id=self.challenge_id,
                locked_by=by,
                occurred_at=occurred_at,
            )
        )

    # -- the refusal both halves make -------------------------------------

    @staticmethod
    def _refuse_a_moment_that_has_gone(
        *, day: date | None, hour: MinuteOfDay | None, now: Instant
    ) -> None:
        """**Refused when the second of the two is filled, in either order.**

        Only the pair is checked. A day on its own names no instant this platform
        will act on — its agreed point is coarsened to the following morning, and
        a game somebody wants to record having played yesterday is a game whose
        day is legitimately behind us. It is the *combination* that claims a
        moment, and only a combination can claim one that has gone.
        """

        if day is None or hour is None:
            return
        if moment_of(day, hour) < now:
            raise ThatMomentHasAlreadyPassed()

    # -- folding ----------------------------------------------------------

    def _record_that(self, event: DomainEvent) -> None:
        self._apply(event)
        self._events.record(event)

    def _apply(self, event: DomainEvent) -> None:
        """Fold one event. **Three are values, one is an act, none is a
        conclusion.**

        **The fold re-runs no refusal.** A stream whose lock precedes its third
        slot cannot be produced by ``lock()`` and would be a bug upstream;
        replaying it loudly would make the plan unreadable — the four people on
        the court would lose the arrangement they can see — rather than making
        the bug visible to anybody who could fix it.
        """

        if isinstance(event, PlaceRecorded):
            # Folded through the value object, so a stored place meets the same
            # rules a new one does — and a row that could not is one this
            # aggregate should refuse to replay silently.
            self.place = Place.of(event.place)
        elif isinstance(event, DayRecorded):
            self.day = date.fromisoformat(event.day)
        elif isinstance(event, HourRecorded):
            self.hour = minute_of_day(event.minute_of_day)
        elif isinstance(event, PlanLocked):
            self.locked_at = instant(event.occurred_at)
        self.version += 1


def _challenge_of(event: DomainEvent) -> UUID:
    """Which challenge an event is about.

    Spelled as a walk over the four rather than as an attribute read, so a fifth
    event added without a challenge id on it is a red test rather than an
    ``AttributeError`` in a fold.
    """

    if isinstance(event, (PlaceRecorded, DayRecorded, HourRecorded, PlanLocked)):
        return event.challenge_id
    raise ValueError(f"not a plan event: {type(event).__name__}")


__all__ = ["SLOTS", "Plan"]
