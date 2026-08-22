"""A half-open interval of instants, and the only place overlap is decided.

**Half-open ``[start, end)``**, the convention `docs/adr/0035` fixed for a
reservation's claimed range and `app/modules/clubs/domain/series.py` already
follows for an effective-dated row: a court freed at 18:00 and taken at 18:00 do
**not** overlap. That is not a detail. It is what lets `turnaroundMin` widen a
claimed interval by padding rather than by arithmetic on somebody else's row —
each reservation claims its own play plus its own turnaround, and back-to-back
claims meet at an instant they do not share.

**One overlap test.** ADR-0035's whole content is that two reservations may not
overlap on one court; the dead repo's `#127` is the same rule written as equality
of a slot's *start*, which lets 14:00–15:30 and 14:30–16:00 both land on court 3.
So the comparison is written once, here, and read by the availability projection,
by every use case and — in the one spelling PostgreSQL understands — by the
exclusion constraint. Three call sites, one meaning.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final

from app.kernel import Instant, Minutes, elapsed_minutes, minutes, shifted


@final
@dataclass(frozen=True)
class TimeRange:
    """From ``start`` up to but not including ``end``.

    A zero-width range is refused rather than represented. It would claim
    nothing — no other range can overlap it — so a reservation carrying one
    would be a court claimed against nobody, which reads as a booking and
    behaves as a gap.
    """

    start: Instant
    end: Instant

    def __post_init__(self) -> None:
        if self.end <= self.start:
            raise ValueError(
                "a time range ends after it begins: "
                f"{self.start.isoformat()} -> {self.end.isoformat()}"
            )

    @property
    def duration(self) -> Minutes:
        """Elapsed minutes, never a wall-clock subtraction — see the kernel."""

        return elapsed_minutes(self.start, self.end)

    def overlaps(self, other: "TimeRange") -> bool:
        """Do these two claim a shared instant. Half-open, so touching is free."""

        return self.start < other.end and other.start < self.end

    def contains(self, moment: Instant) -> bool:
        return self.start <= moment < self.end

    def widened_by(self, span: Minutes) -> "TimeRange":
        """The same play, claiming ``span`` more minutes after it.

        **After it, and never before.** A turnaround is the gap a club needs
        *between* reservations, and padding both ends would charge that gap
        twice — once to the reservation that ends and once to the one that
        begins — which is a court sitting empty for two turnarounds and a club
        wondering where its hour went. Padding the tail alone composes: every
        reservation claims its own turnaround, and the next one may begin the
        instant that claim ends.
        """

        if span < 0:
            raise ValueError(f"a turnaround below zero: {span}")
        return TimeRange(start=self.start, end=shifted(self.end, span))


def span(start: Instant, length: Minutes) -> TimeRange:
    """A range from ``start`` lasting ``length`` — the way a slot is quoted."""

    return TimeRange(start=start, end=shifted(start, minutes(length)))
