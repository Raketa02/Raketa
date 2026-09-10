"""The Plan context's domain events — **three recordings and one act.**

``docs/adr/0144`` and ``docs/adr/0155``. A place recorded, a day recorded, an
hour recorded — each carrying the value, the player and the moment — and, beside
them, a plan **locked**.

**Setting a slot and moving one are the same event told with two sentences**,
separated by the fold rather than by a second class. Unlike a lapse and a
decline, which do the same thing to a line-up and are different facts, these are
one fact told twice — so a ``DayChanged`` beside ``DayRecorded`` would be two
names for one thing and the room would have to know which sentence to write.

**There is no opening event.** A plan is *born by being used*: nothing is written
at birth, there is no subscriber to ``GamePlanned``, and *no plan* is what a game
with nothing agreed draws. The first recording is the birth, and the aggregate id
is the game's.

**There is still no completion event, and ``PlanLocked`` is emphatically not
one** — the distinction is the whole of ``docs/adr/0155``. The third recording
*is* the completion, and an event announcing it would be a conclusion the record
already implies. A lock is the opposite kind of fact: **nobody wrote it down**,
so no arrangement of the three slots reaches it, which is exactly the test
``docs/adr/0142`` §3 makes an event pass before it may announce anything. The
count says a plan *could* be agreed; the lock says somebody agreed it.

**There is no clearing event, no cancellation and no unlock.** A slot is never
emptied and a plan is never unmade: nobody turns up, and the game ghosts at
``NEVER_PLAYED``. There is no ``PlanUnlocked`` for the same reason there is no
clearing event — the lock is a thing that happened, and a later move re-agrees it
rather than un-agreeing it (``docs/adr/0145`` §5).

**Nothing derived is here.** Not the slot count, not the agreed point. Both are
folded from the three recordings, which is what *stores nothing it can derive*
means in a context whose whole record is four facts.

Events carry **primitive** fields, so their wire format survives any later
refactor of the Python types: a player as a ``str`` uuid, a local date as its
ISO spelling, an hour as a minute of the local day. The date is a string and not
a ``date`` because the codec coerces exactly two types back — ``UUID`` and
``datetime`` — and a third that encoded but did not decode would be a stream that
folds wrongly rather than loudly.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class PlaceRecorded:
    """Somebody wrote down where. **The value as they typed it**, one line."""

    game_id: UUID
    place: str
    recorded_by: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class DayRecorded:
    """Somebody wrote down which day. **A local date in the platform zone.**

    ISO-spelled — ``YYYY-MM-DD`` — because a stored day offset is a number whose
    meaning moves with its anchor, and this one has to mean the same thing on
    every reader's clock for ever.
    """

    game_id: UUID
    day: str
    recorded_by: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class HourRecorded:
    """Somebody wrote down what time. **A minute of the local day.**

    The integer coordinate rather than a wall-clock string, because that is what
    the one conversion takes: ``slot_start`` turns a day and a minute into an
    instant, and a stored ``"18:00"`` would be parsed back into this on the way
    in to it.
    """

    game_id: UUID
    minute_of_day: int
    recorded_by: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class PlanLocked:
    """Somebody agreed the plan. **An act, and it carries no value.**

    ``docs/adr/0155``. The value is the three slots and they are already
    recorded; repeating one here would be the second place it is true, and the
    first thing to disagree with the slot beside it after a later move.

    **It freezes nothing.** Any member may still move a slot afterwards, and each
    move writes its own event exactly as it did before — so this is a fact about
    a moment rather than a state the aggregate then enforces.
    """

    game_id: UUID
    locked_by: UUID
    occurred_at: datetime


__all__ = ["DayRecorded", "HourRecorded", "PlaceRecorded", "PlanLocked"]
