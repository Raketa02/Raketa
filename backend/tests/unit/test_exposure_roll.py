"""The roll's arithmetic: what *shown more often than most* means this week.

Pure, and tested against counts rather than against a store, because the
percentile is the only thing in the exposure roll that can be wrong in a way a
job's logs would not show.
"""

from __future__ import annotations

import pytest

from app.kernel import InvariantViolated
from app.modules.matchmaking.domain.exposure_roll import (
    EXPOSURE_BUSY_PERCENTILE,
    busy_threshold_of,
)


def test_the_percentile_is_the_one_the_spec_names():
    assert EXPOSURE_BUSY_PERCENTILE == 90


def test_an_empty_week_has_no_threshold():
    """Nobody was shown, so *more often than most* is not a question yet.

    ``None`` rather than zero: a zero would make every player with no
    appearances *busier than most*, which would dock the whole pool in the one
    state the exposure floor exists to lift them out of.
    """

    assert busy_threshold_of([]) is None


def test_one_player_is_their_own_ninetieth_percentile():
    assert busy_threshold_of([7]) == 7


def test_the_threshold_is_a_count_that_somebody_actually_has():
    """Nearest-rank, never interpolated.

    An interpolated percentile over ten integers lands between two of them, and
    a threshold of 4.6 appearances is a number nobody can have and no log line
    can be read against. The rung is *shown more than this many times*, so the
    bound has to be one of the counts in the bucket.
    """

    counts = [1, 1, 2, 2, 3, 3, 4, 5, 8, 40]

    assert busy_threshold_of(counts) == 8


def test_order_does_not_change_the_answer():
    counts = [4, 40, 1, 8, 2, 3, 1, 5, 2, 3]

    assert busy_threshold_of(counts) == busy_threshold_of(sorted(counts))


def test_the_same_bucket_rolls_to_the_same_threshold():
    """Idempotence, at the only place in the roll that computes anything.

    The job is registered under ``docs/adr/0092``, so it runs N times per
    interval across N processes at unrelated moments. What makes that safe is
    that a re-run over an unchanged bucket publishes the identical scalar rather
    than one that drifts.
    """

    counts = [1, 2, 2, 9, 9, 30]

    assert busy_threshold_of(counts) == busy_threshold_of(counts)


@pytest.mark.parametrize(
    ("counts", "expected"),
    [
        ([5, 5, 5, 5], 5),
        ([1, 2], 2),
        ([1] * 8 + [99], 99),
        ([1] * 9 + [99], 1),
        ([1, 1, 1, 1, 1, 1, 1, 2, 9, 30], 9),
    ],
    ids=[
        "everybody-equal",
        "two-players",
        "one-outlier-in-nine",
        "one-outlier-in-ten",
        "a-real-tail",
    ],
)
def test_the_tail_the_rung_is_meant_to_catch(counts, expected):
    """The rung docks *the busy tenth*, never *the busiest player*.

    The third and fourth rows are the boundary and are the reason this is
    parameterised at all. With one heavy player among **nine** the ninetieth
    percentile is still that player, so nobody is above it and the rung docks
    nobody; add one more ordinary player and the percentile drops onto the flat
    part of the distribution, where the outlier is finally above it. That is the
    intended behaviour — the dock exists to relieve concentration, and a pool
    too small to have a concentrated tenth has nothing to relieve.
    """

    assert busy_threshold_of(counts) == expected


def test_a_negative_count_is_refused():
    """A count below zero is a caller's bug, not a lossy read."""

    with pytest.raises(InvariantViolated):
        busy_threshold_of([1, -1])
