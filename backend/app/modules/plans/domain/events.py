"""The Plan context's domain events — **three, and there are no others.**

``docs/adr/0144``. A place recorded, a day recorded, an hour recorded, each
carrying the value, the player and the moment.

**Setting a slot and moving one are the same event told with two sentences**,
separated by the fold rather than by a second class. Unlike a lapse and a
decline, which do the same thing to a line-up and are different facts, these are
one fact told twice — so a ``DayChanged`` beside ``DayRecorded`` would be two
names for one thing and the room would have to know which sentence to write.

**There is no opening event.** A plan is *born by being used*: nothing is written
at birth, there is no subscriber to ``GamePlanned``, and *no plan* is what a game
with nothing agreed draws. The first recording is the birth, and the aggregate id
is the game's.

**There is no completion event, no clearing event and no cancellation.** The
third recording *is* the completion, and a line announcing it would be a
conclusion the record already implies — ``challenges``' rule and ``games``'
identical one. A slot is never emptied and a plan is never unmade: nobody turns
up, and the game ghosts at ``NEVER_PLAYED``.

**Nothing derived is here.** Not the slot count, not the agreed point. Both are
folded from these three, which is what *stores nothing it can derive* means in a
context whose whole record is three facts.

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


__all__ = ["DayRecorded", "HourRecorded", "PlaceRecorded"]
