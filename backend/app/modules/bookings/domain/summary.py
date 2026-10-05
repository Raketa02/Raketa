"""The club's day of new bookings, summed up once (#548; the mechanics §16.12,
the screens B9).

**A new booking is told to the club once a day, never one by one**: at the close
of each club day (``last_closed_day``), the desk is sent every game booked at
the club since the close before — and nothing on a day nothing was booked. The
summary is a stream of its own, **one per club per day**, born with the one
event that says it was sent: its id is the club and the day, so two processes
summing up the same day collide on it, and the job needs no lock.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date
from typing import Final
from uuid import UUID, uuid5

from app.kernel import Instant, invariant
from app.modules.bookings.domain.events import NewBookingsSummarised
from app.shared.domain import DomainEvent
from app.shared.domain.events import EventRecorder

#: What a club day's summary id is drawn under — fixed for ever, since a stored
#: stream is found by it.
_SUMMARIES: Final = UUID("2d6b8f0e-7c1a-4a55-9b3e-0f4c6a1d8e27")


def summary_id_for(club_id: UUID, day: date) -> UUID:
    """The summary of the club's new bookings on ``day`` — one at most."""

    return uuid5(_SUMMARIES, f"{club_id}:{day.isoformat()}")


@dataclass
class NewBookingsSummary:
    summary_id: UUID
    club_id: UUID
    day: date
    booking_ids: tuple[UUID, ...]
    version: int = 0
    _events: EventRecorder = field(
        default_factory=EventRecorder, init=False, repr=False, compare=False
    )

    @classmethod
    def sent(
        cls,
        *,
        club_id: UUID,
        day: date,
        booking_ids: tuple[UUID, ...],
        at: Instant,
    ) -> "NewBookingsSummary":
        invariant(bool(booking_ids), "a summary of no bookings")
        event = NewBookingsSummarised(
            summary_id=summary_id_for(club_id, day),
            club_id=club_id,
            day=day.isoformat(),
            booking_ids=booking_ids,
            occurred_at=at,
        )
        summary = cls._born(event)
        summary._events.record(event)
        return summary

    @classmethod
    def from_history(cls, events: Iterable[DomainEvent]) -> "NewBookingsSummary":
        opening = next(iter(events))
        invariant(
            isinstance(opening, NewBookingsSummarised),
            f"a new bookings summary stream opens {opening!r}",
        )
        assert isinstance(opening, NewBookingsSummarised)
        return cls._born(opening)

    @classmethod
    def _born(cls, opening: NewBookingsSummarised) -> "NewBookingsSummary":
        return cls(
            summary_id=opening.summary_id,
            club_id=opening.club_id,
            day=date.fromisoformat(opening.day),
            booking_ids=opening.booking_ids,
            version=1,
        )

    def pull_events(self) -> list[DomainEvent]:
        return self._events.pull()
