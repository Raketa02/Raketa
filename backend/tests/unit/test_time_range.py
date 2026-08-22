"""Half-open intervals, and the one place overlap is decided.

Small, and load-bearing out of all proportion to its size: this is the rule the
exclusion constraint enforces on PostgreSQL and the availability projection
enforces in memory, and the two must mean the same thing. The dead repo's `#127`
is what happens when they do not — a uniqueness rule about a slot's *start* lets
14:00–15:30 and 14:30–16:00 both land on court 3.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.kernel import hours, instant, minutes
from app.modules.courts.domain.time_range import TimeRange, span


def at(hour: int, minute: int = 0):
    return instant(datetime(2026, 9, 1, hour, minute, tzinfo=timezone.utc))


SIX_TO_SEVEN_THIRTY = TimeRange(start=at(18), end=at(19, 30))


def test_a_range_ends_after_it_begins():
    with pytest.raises(ValueError, match="ends after it begins"):
        TimeRange(start=at(19), end=at(18))


def test_a_zero_width_range_is_refused():
    """It would claim nothing, so nothing could overlap it — a court claimed
    against nobody, which reads as a booking and behaves as a gap."""

    with pytest.raises(ValueError, match="ends after it begins"):
        TimeRange(start=at(18), end=at(18))


def test_overlapping_ranges_overlap_both_ways_round():
    later = TimeRange(start=at(19), end=at(20))
    assert SIX_TO_SEVEN_THIRTY.overlaps(later)
    assert later.overlaps(SIX_TO_SEVEN_THIRTY)


def test_a_range_inside_another_overlaps_it():
    """`#127` from the other side: containment is not equality of start."""

    inside = TimeRange(start=at(18, 30), end=at(19))
    assert SIX_TO_SEVEN_THIRTY.overlaps(inside)
    assert inside.overlaps(SIX_TO_SEVEN_THIRTY)


def test_ranges_that_only_touch_do_not_overlap():
    """The half-open convention, and the reason turnaround can be padding.

    A court freed at 19:30 and taken at 19:30 are two bookings, not a conflict.
    """

    next_up = TimeRange(start=at(19, 30), end=at(21))
    assert not SIX_TO_SEVEN_THIRTY.overlaps(next_up)
    assert not next_up.overlaps(SIX_TO_SEVEN_THIRTY)


def test_a_range_contains_its_start_and_not_its_end():
    assert SIX_TO_SEVEN_THIRTY.contains(at(18))
    assert SIX_TO_SEVEN_THIRTY.contains(at(19, 29))
    assert not SIX_TO_SEVEN_THIRTY.contains(at(19, 30))


def test_duration_is_elapsed_minutes():
    assert SIX_TO_SEVEN_THIRTY.duration == minutes(90)


def test_widening_moves_the_end_and_never_the_start():
    """A turnaround is the gap *after* play. Padding both ends would charge the
    club for two turnarounds between every pair of bookings."""

    widened = SIX_TO_SEVEN_THIRTY.widened_by(minutes(15))

    assert widened.start == SIX_TO_SEVEN_THIRTY.start
    assert widened.end == at(19, 45)


def test_widening_by_nothing_is_the_same_range():
    assert SIX_TO_SEVEN_THIRTY.widened_by(minutes(0)) == SIX_TO_SEVEN_THIRTY


def test_widened_claims_still_meet_without_overlapping():
    """Two back-to-back reservations, each padded fifteen minutes, compose.

    The second may start the instant the first's claim ends — which is what
    makes padding the tail alone sufficient, and what would stop being true if
    the range were closed at both ends.
    """

    first = span(at(18), minutes(90)).widened_by(minutes(15))
    second = span(at(19, 45), minutes(90)).widened_by(minutes(15))

    assert not first.overlaps(second)
    assert first.end == second.start


def test_a_negative_turnaround_is_refused():
    with pytest.raises(ValueError, match="turnaround below zero"):
        SIX_TO_SEVEN_THIRTY.widened_by(minutes(-15))


def test_span_quotes_a_slot_from_its_start_and_length():
    assert span(at(18), hours(2)) == TimeRange(start=at(18), end=at(20))
