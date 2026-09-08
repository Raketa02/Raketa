"""The Plan aggregate — one game's three slots, event-sourced.

**Where and when these people are meeting.** It is *one game's*, identified by
that game's id, and it sits between the two contexts either side of it:
``challenges`` ends at *everybody has answered* and ``games`` begins at *played*,
and this belongs to neither (``docs/adr/0144``).

Four things about it are load-bearing and none is obvious from the code alone.

**It is born by being used.** There is no opening event, no record at birth and
no subscriber to ``GamePlanned``: ``unwritten`` is what a game with nothing
agreed has, and it is a real state rather than a placeholder — the write path
starts from it, and the read never meets one, because a game nobody has agreed
anything about has no stream for the directory to return.

There is **no flag saying whether anything has been agreed**, and the reason is
that nothing would ask: the write path starts from an unwritten plan whatever it
holds, and the read spells absence by having no stream to fold. A property that
only a test reads is a claim about a shape nothing checks.

**Its id is the game's**, so there is one plan per game for ever. A second id
would be a second name for the same thing, and it would need a lookup by payload
to be found; keying on the game's id makes the stream read an equality on the
aggregate id and makes *one game, one plan* a fact about the store rather than a
rule a caller keeps.

**Nothing derived is stored.** Not the slot count, not the agreed point. Both are
properties folded from the three values, and ``planned_at`` is **never written**
— it keeps meaning *when it became a game*, and the plan never writes to
``games`` at all.

**Any member may fill or change any slot, any number of times, and a slot is
never emptied.** There is no history beyond the system lines each change writes
and no rate limit — *the line is the friction*. Last write wins, so a plan can be
moved under somebody who has already read it, and that is accepted: the
alternative is a proposal each person accepts, which is the negotiation this card
exists not to be.

**Who may write at all is not decided here.** *Is this player on this game's
court, and is that game still open to planning* is one question asked of
``games`` through one port, and the two refusals it produces belong to the use
case that asks it. What this aggregate refuses is about the **values** — a day
past the horizon, an hour nobody offered, a moment that has gone.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from datetime import time as wall_time
from typing import Iterable
from uuid import UUID

from app.kernel import Instant, MinuteOfDay, minute_of_day
from app.modules.plans.domain.errors import ThatMomentHasAlreadyPassed
from app.modules.plans.domain.events import (
    DayRecorded,
    HourRecorded,
    PlaceRecorded,
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

#: How many slots there are. Spelled once, because *filling the third is the
#: lock* and there is no lock — so the only thing this number is ever used for is
#: saying how far along a plan is.
SLOTS = 3


@dataclass
class Plan:
    """One game's plan, rebuilt by folding its stream."""

    game_id: UUID
    place: Place | None
    day: date | None
    hour: MinuteOfDay | None
    version: int = 0
    _events: EventRecorder = field(
        default_factory=EventRecorder, init=False, repr=False, compare=False
    )

    @property
    def id(self) -> UUID:
        """The stream id, which **is** the game's id."""

        return self.game_id

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

    def pull_events(self) -> list[DomainEvent]:
        return self._events.pull()

    # -- birth ------------------------------------------------------------

    @classmethod
    def unwritten(cls, game_id: UUID) -> "Plan":
        """The plan a game with nothing agreed has.

        **Not a factory for an empty record**, because no record is written: it
        is the value the repository answers with when a stream is empty, and the
        first recording below is what brings it into existence.
        """

        return cls(game_id=game_id, place=None, day=None, hour=None)

    @classmethod
    def from_history(cls, events: Iterable[DomainEvent]) -> "Plan":
        """Rebuild from the stream. **Any of the three may be the first event.**

        There is no opening event to construct from, so the game id is read off
        whichever recording happens to be first — every one of the three carries
        it, because every one of them can be a birth.
        """

        plan: Plan | None = None
        for event in events:
            if plan is None:
                plan = cls.unwritten(_game_of(event))
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
                game_id=self.game_id,
                place=written.value,
                recorded_by=by,
                occurred_at=occurred_at,
            )
        )

    def record_day(
        self, *, day: date, by: UUID, planned_at: Instant, occurred_at: Instant
    ) -> None:
        """*We are playing on this day.*

        Two refusals, in this order and deliberately: **the clamp** first, because
        a day past the horizon is not a day this plan may hold at all; then **the
        past combination**, which only exists once an hour is already recorded.

        ``planned_at`` is the game's and arrives from the caller. It is the one
        fact this aggregate borrows, and it is borrowed rather than stored
        because the plan never writes to ``games`` and must not hold a copy of
        anything it does.
        """

        if day == self.day:
            return
        refuse_a_day_past_the_horizon(day, planned_at=planned_at)
        self._refuse_a_moment_that_has_gone(day=day, hour=self.hour, now=occurred_at)
        self._record_that(
            DayRecorded(
                game_id=self.game_id,
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
                game_id=self.game_id,
                minute_of_day=int(offered),
                recorded_by=by,
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
        """Fold one event. **All three are values and none is a conclusion.**"""

        if isinstance(event, PlaceRecorded):
            # Folded through the value object, so a stored place meets the same
            # rules a new one does — and a row that could not is one this
            # aggregate should refuse to replay silently.
            self.place = Place.of(event.place)
        elif isinstance(event, DayRecorded):
            self.day = date.fromisoformat(event.day)
        elif isinstance(event, HourRecorded):
            self.hour = minute_of_day(event.minute_of_day)
        self.version += 1


def _game_of(event: DomainEvent) -> UUID:
    """Which game a recording is about.

    Spelled as a walk over the three rather than as an attribute read, so a
    fourth event added without a game id on it is a red test rather than an
    ``AttributeError`` in a fold.
    """

    if isinstance(event, (PlaceRecorded, DayRecorded, HourRecorded)):
        return event.game_id
    raise ValueError(f"not a plan event: {type(event).__name__}")


__all__ = ["SLOTS", "Plan"]
