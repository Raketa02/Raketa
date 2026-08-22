"""The effective-dated series: one open row, half-open intervals, no rewrites.

This is the mechanism all three of ADR-0077's history-bearing facts share, so
every property here is a property of the policy series, the payout series and the
court catalogue at once. The database enforces the same invariant with a partial
unique index; this type is what stops the wrong state being *constructed*, which
is the half an index cannot reach.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.kernel import instant
from app.modules.clubs.domain.series import Series, Version, series_from
from app.modules.clubs.domain.value_objects import SYSTEM, ChangedBy

FRIDAY_1600 = instant(datetime(2026, 9, 4, 16, 0, tzinfo=timezone.utc))
FRIDAY_1800 = instant(datetime(2026, 9, 4, 18, 0, tzinfo=timezone.utc))
SATURDAY = instant(datetime(2026, 9, 5, 10, 0, tzinfo=timezone.utc))
THURSDAY = instant(datetime(2026, 9, 3, 10, 0, tzinfo=timezone.utc))


def test_a_new_series_has_one_open_row():
    series = series_from("48h", at=FRIDAY_1600)

    assert series.current == "48h"
    assert series.open_version is not None
    assert series.open_version.valid_to is None
    assert len(series) == 1


def test_opening_a_version_closes_the_one_in_force():
    series = series_from("48h", at=THURSDAY).opened("6h", at=FRIDAY_1600)

    assert [version.value for version in series] == ["48h", "6h"]
    assert series.versions[0].valid_to == FRIDAY_1600
    assert series.versions[1].valid_from == FRIDAY_1600
    assert series.current == "6h"


def test_only_the_last_version_may_be_open():
    """The invariant the partial unique index enforces, in memory."""

    with pytest.raises(ValueError, match="only one open version"):
        Series(
            (
                Version("48h", valid_from=THURSDAY),
                Version("6h", valid_from=FRIDAY_1600),
            )
        )


def test_versions_may_not_overlap():
    with pytest.raises(ValueError, match="may not overlap"):
        Series(
            (
                Version("48h", valid_from=THURSDAY, valid_to=FRIDAY_1800),
                Version("6h", valid_from=FRIDAY_1600),
            )
        )


def test_a_version_may_not_end_before_it_began():
    with pytest.raises(ValueError, match="cannot end before it began"):
        Version("48h", valid_from=FRIDAY_1800, valid_to=FRIDAY_1600)


def test_the_interval_is_half_open_so_the_change_instant_has_one_answer():
    """*What was the hold cap on Friday at 16:00* is one row, not two and not
    none — including at the exact instant of the change."""

    series = series_from("48h", at=THURSDAY).opened("6h", at=FRIDAY_1600)

    assert series.as_of(THURSDAY) == "48h"
    assert series.as_of(FRIDAY_1600) == "6h"
    assert series.as_of(FRIDAY_1800) == "6h"
    matching = [v for v in series if v.contains(FRIDAY_1600)]
    assert len(matching) == 1


def test_nothing_is_in_force_before_the_series_began():
    series = series_from("48h", at=FRIDAY_1600)

    assert series.as_of(THURSDAY) is None
    assert series.as_of(FRIDAY_1800) == "48h"


def test_closing_a_series_leaves_history_and_no_row_in_force():
    """A retired court: the open row is closed and nothing opens. ADR-0079's
    *retired, never deleted* — the record still parses."""

    series = series_from("Court 3", at=THURSDAY).closed(at=FRIDAY_1600)

    assert series.current is None
    assert series.open_version is None
    assert len(series) == 1
    assert series.as_of(THURSDAY) == "Court 3"
    assert series.as_of(FRIDAY_1800) is None


def test_reopening_a_closed_series_is_allowed_and_leaves_a_gap():
    """A court taken out of the catalogue and put back is two live intervals with
    a hole between them, which is exactly what happened."""

    series = (
        series_from("Mondo", at=THURSDAY)
        .closed(at=FRIDAY_1600)
        .opened("Wall", at=SATURDAY)
    )

    assert series.current == "Wall"
    assert series.as_of(FRIDAY_1800) is None
    assert len(series) == 2


def test_closing_an_already_closed_series_changes_nothing():
    """Idempotent, so a re-save cannot rewrite the instant a version ended."""

    closed = series_from("Court 3", at=THURSDAY).closed(at=FRIDAY_1600)

    assert closed.closed(at=SATURDAY) == closed


def test_a_version_cannot_be_closed_before_it_opened():
    series = series_from("48h", at=FRIDAY_1600)

    with pytest.raises(ValueError, match="cannot be closed"):
        series.closed(at=THURSDAY)
    with pytest.raises(ValueError, match="cannot be closed"):
        series.opened("6h", at=THURSDAY)


def test_a_series_is_immutable_so_a_change_cannot_be_half_applied():
    original = series_from("48h", at=THURSDAY)

    changed = original.opened("6h", at=FRIDAY_1600)

    assert original.current == "48h"
    assert changed.current == "6h"
    assert len(original) == 1


def test_every_row_carries_an_actor_and_it_reads_system():
    series = series_from("48h", at=THURSDAY).opened("6h", at=FRIDAY_1600)

    assert all(version.changed_by == SYSTEM for version in series)
    assert all(version.changed_by.is_system for version in series)


def test_a_named_actor_is_carried_when_one_is_given():
    """The column is ready for a console; nothing in `app/` writes one yet."""

    ops = ChangedBy("ops@raketa")
    series = series_from("48h", at=THURSDAY, changed_by=ops)

    assert series.versions[0].changed_by == ops
    assert not ops.is_system


def test_closing_keeps_the_actor_that_opened_the_row():
    """A close is always half of something else, so it records no actor of its
    own — the row still says who authored what it held."""

    ops = ChangedBy("ops@raketa")
    series = series_from("48h", at=THURSDAY, changed_by=ops).opened(
        "6h", at=FRIDAY_1600
    )

    assert series.versions[0].changed_by == ops
    assert series.versions[1].changed_by == SYSTEM
