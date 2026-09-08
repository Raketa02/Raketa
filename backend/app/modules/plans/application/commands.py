"""What a caller sends to change or read a plan.

**Three commands and not one with a slot code**, because ADR-0144 has three
events and each carries a different kind of value: a line of text, a local date
and a minute of the local day. One command with a ``slot`` field and a ``str``
value would put the parsing back in the use case and lose the type at the one
boundary that has three of them.

**None of them carries an instant.** The moment a slot was recorded is the
clock's, read once inside the use case, exactly as every other write in this
repository takes its own.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from datetime import time as wall_time
from typing import final
from uuid import UUID


@final
@dataclass(frozen=True, slots=True)
class ReadPlansCommand:
    """*The plans of every game I am on the court of.*"""

    reader_id: UUID


@final
@dataclass(frozen=True, slots=True)
class SetPlaceCommand:
    """*We are meeting here.*"""

    game_id: UUID
    player_id: UUID
    place: str


@final
@dataclass(frozen=True, slots=True)
class SetDayCommand:
    """*We are playing on this day* — a local date in the platform zone."""

    game_id: UUID
    player_id: UUID
    day: date


@final
@dataclass(frozen=True, slots=True)
class SetHourCommand:
    """*We are playing at this time* — a local clock time in the platform zone."""

    game_id: UUID
    player_id: UUID
    hour: wall_time


__all__ = [
    "ReadPlansCommand",
    "SetDayCommand",
    "SetHourCommand",
    "SetPlaceCommand",
]
