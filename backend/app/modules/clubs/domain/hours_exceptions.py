"""An exception: hours a club closes without touching its weekly pattern — a
tournament, a holiday, a repair (the mechanics §16.5, the screens B3).

**A local day or a run of them, whole or between two hours, on every court or
some.** One shape covers the three the desk is offered — *a date*, *a range*,
*hours on a date* — and the hours, where given, close on each day of the run.
*Every court* means every court the club has **at the time an hour is read**, a
court added later included: a tournament closes the club, not a list.

A reason is kept **for the club's own records** and is the label its list shows
(*Tournament · 4–5 Oct · all courts*). No player reads it.

**What an exception is over is decided here and nowhere else** (``covers``), so
the refusal over a booking and the derivation of what a club can sell cannot
come to two answers about one hour.
"""

from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass
from datetime import date
from typing import Final, final
from uuid import UUID

from app.kernel import Instant
from app.modules.clubs.domain.court_hours import (
    DAY_CLOSES,
    DAY_OPENS,
    local_day,
    local_hour,
    within_the_day,
)
from app.modules.clubs.domain.errors import (
    ExceptionCourtsRequired,
    ExceptionDaysInvalid,
    ExceptionHoursInvalid,
    ExceptionInThePast,
    ExceptionReasonInvalid,
)

#: The longest reason, in characters: a label in the desk's own list.
EXCEPTION_REASON_LONGEST: Final = 80


@final
@dataclass(frozen=True, slots=True)
class ExceptionReason:
    """Why the club closed these hours, as the desk wrote it: trimmed, runs of
    whitespace collapsed, 1–80 characters."""

    value: str

    def __post_init__(self) -> None:
        collapsed = " ".join(self.value.split())
        if not 1 <= len(collapsed) <= EXCEPTION_REASON_LONGEST:
            raise ExceptionReasonInvalid()
        object.__setattr__(self, "value", collapsed)


@final
@dataclass(frozen=True, slots=True)
class ClosedHours:
    """From ``opens`` until ``closes`` on each day — 09 and 12 close
    09:00–12:00, three court hours. Within the grid, and at least one hour."""

    opens: int
    closes: int

    def __post_init__(self) -> None:
        if not within_the_day(self.opens, self.closes):
            raise ExceptionHoursInvalid()

    @classmethod
    def of(cls, opens: int | None, closes: int | None) -> "ClosedHours | None":
        """Both or neither: neither is the whole day, one alone says nothing
        the desk can have meant."""

        if opens is None and closes is None:
            return None
        if opens is None or closes is None:
            raise ExceptionHoursInvalid()
        return cls(opens=opens, closes=closes)

    def holds(self, hour: int) -> bool:
        return self.opens <= hour < self.closes


@final
@dataclass(frozen=True, slots=True)
class HoursException:
    """One exception, as the club's stream leaves it."""

    id: UUID
    #: The courts it closes **in the club's order**, or ``None`` for **every**
    #: court the club has. The club's order never changes for a court that
    #: stays, so a tuple recorded once is still in it after any deletion.
    court_ids: tuple[UUID, ...] | None
    first_day: date
    last_day: date
    #: The hours it closes on each day, or ``None`` for the whole day.
    hours: ClosedHours | None
    reason: ExceptionReason

    def __post_init__(self) -> None:
        if self.first_day > self.last_day:
            raise ExceptionDaysInvalid()
        if self.court_ids is not None and not self.court_ids:
            raise ExceptionCourtsRequired()

    def refuse_if_over(self, *, today: date) -> None:
        """Closing days already gone changes nothing a player or a desk will
        ever read, so it is refused rather than stored as a row nobody sees."""

        if self.last_day < today:
            raise ExceptionInThePast()

    def is_over(self, *, today: date) -> bool:
        return self.last_day < today

    @property
    def span(self) -> tuple[int, int]:
        """The hours it closes on each of its days, the whole day included."""

        if self.hours is None:
            return DAY_OPENS, DAY_CLOSES
        return self.hours.opens, self.hours.closes

    def covers(self, court_id: UUID, start: Instant) -> bool:
        """Whether the court hour on ``court_id`` from ``start`` is closed by
        this exception. A court hour starts on the hour, so it is closed exactly
        when the hour it starts at is."""

        if self.court_ids is not None and court_id not in self.court_ids:
            return False
        if not self.first_day <= local_day(start) <= self.last_day:
            return False
        return self.hours is None or self.hours.holds(local_hour(start))

    def without(self, court_ids: Collection[UUID]) -> "HoursException | None":
        """This exception with these courts no longer named — ``None`` when it
        named only them, since it then closes nothing. *Every court* is
        untouched: it never named any."""

        if self.court_ids is None:
            return self
        remaining = tuple(
            court_id for court_id in self.court_ids if court_id not in court_ids
        )
        if not remaining:
            return None
        return HoursException(
            id=self.id,
            court_ids=remaining,
            first_day=self.first_day,
            last_day=self.last_day,
            hours=self.hours,
            reason=self.reason,
        )
