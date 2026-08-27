"""Two budgets, not one, and only one of them changes what a search does.

§17's *p50 2 s, p99 15 s* is a **target on the refresh loop**: missing it raises
an alert and changes no behaviour. §18's *15 min / 24 h* is a **degradation
ladder**, and it stands on **quality** rather than safety — ``docs/adr/0095``,
``docs/adr/0098`` and ``docs/adr/0109`` between them took every live-truth fact
out of the index, so there is nothing safety-critical left in it for a refusal to
protect. What a day-old index means is stale μ, stale grids and stale intent, and
a shortlist built from those is a confident bad list (``docs/adr/0111``).

Reading the two as one number is the mistake this file exists to make
impossible.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from app.modules.matchmaking.domain.index_staleness import (
    IndexFreshness,
    REFRESH_TARGET_P99,
    freshness_of,
    misses_refresh_target,
)


@pytest.mark.parametrize(
    ("lag", "expected"),
    [
        (timedelta(0), IndexFreshness.FRESH),
        (timedelta(seconds=2), IndexFreshness.FRESH),
        (timedelta(minutes=14, seconds=59), IndexFreshness.FRESH),
        (timedelta(minutes=15), IndexFreshness.STALE),
        (timedelta(hours=23, minutes=59), IndexFreshness.STALE),
        (timedelta(hours=24), IndexFreshness.REFUSED),
        (timedelta(days=3), IndexFreshness.REFUSED),
    ],
)
def test_the_ladder_has_three_rungs_and_the_boundaries_are_where_they_say(
    lag: timedelta, expected: IndexFreshness
) -> None:
    assert freshness_of(lag) is expected


def test_the_middle_rung_serves_and_records_rather_than_refusing() -> None:
    """*Serve, record ``index_stale``, alarm* — and show the player nothing.

    The flag is **internal**: it goes on the search record and into the
    structured logs, never onto the wire envelope. §18 itself says the player
    sees nothing at that rung, so a field on the contract would ship with no
    consumer.
    """

    stale = freshness_of(timedelta(hours=1))
    assert stale.serves is True
    assert stale.records_staleness is True


def test_the_bottom_rung_is_the_only_one_that_refuses() -> None:
    refused = freshness_of(timedelta(hours=30))
    assert refused.serves is False


def test_the_top_rung_records_nothing() -> None:
    """An honest fresh index has nothing to say about itself."""

    fresh = freshness_of(timedelta(seconds=3))
    assert (fresh.serves, fresh.records_staleness) == (True, False)


def test_a_negative_lag_reads_fresh_rather_than_raising() -> None:
    """Two clocks disagreeing by a second is not a reason to stop serving."""

    assert freshness_of(timedelta(seconds=-5)) is IndexFreshness.FRESH


@pytest.mark.parametrize(
    ("lag", "misses"),
    [
        (timedelta(seconds=2), False),
        (timedelta(seconds=REFRESH_TARGET_P99), False),
        (timedelta(seconds=REFRESH_TARGET_P99 + 0.1), True),
    ],
)
def test_the_refresh_target_is_missed_only_past_the_p99(
    lag: timedelta, misses: bool
) -> None:
    assert misses_refresh_target(lag) is misses


def test_missing_the_refresh_target_is_not_a_rung_of_the_ladder() -> None:
    """The two budgets are separate, and this is the assertion that keeps them so.

    A lag that misses §17's p99 by an order of magnitude is still nowhere near
    §18's first rung, and reading them as one number is what made the map treat a
    service level as a failure mode for as long as it did.
    """

    lag = timedelta(seconds=60)
    assert misses_refresh_target(lag) is True
    assert freshness_of(lag) is IndexFreshness.FRESH
