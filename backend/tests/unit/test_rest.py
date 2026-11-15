"""The rest rule (#796; ``docs/adr/0204`` §7, §10; the home-rows mechanics §9.2):
**five different Warsaw days on screen**, counted only while the pair is still
unconnected, rest a player in that row; a rested player is a gap, never hidden.
Pure, so held here; the counting itself is the route's
(``tests/api/test_rows_stay_alive.py``)."""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from app.kernel import instant
from app.modules.discovery.domain.fresh_then_gaps import FreshThenGaps
from app.modules.discovery.domain.relation import Relation
from app.modules.discovery.domain.rest import (
    RESTS_AFTER,
    OnScreenRow,
    counts_toward_rest,
    day_on_screen,
    has_rested,
)


def test_five_different_days_rest_a_player_and_four_do_not():
    assert RESTS_AFTER == 5
    assert not has_rested(0)
    assert not has_rested(4)
    assert has_rested(5)
    # The count never resets, and a day past the fifth is still rested.
    assert has_rested(9)


def test_a_day_on_screen_is_the_warsaw_day():
    # 23:30 in UTC on the 14th is half past midnight on the 15th in Warsaw.
    late = instant(datetime(2026, 11, 14, 23, 30, tzinfo=timezone.utc))
    early = instant(datetime(2026, 11, 14, 22, 59, tzinfo=timezone.utc))

    assert day_on_screen(late) == date(2026, 11, 15)
    assert day_on_screen(early) == date(2026, 11, 14)


@pytest.mark.parametrize(
    ("relation", "counts"),
    [
        (Relation.NONE, True),
        # Somebody who asked the reader is not connected: fresh, so resting.
        (Relation.ASKED_YOU, True),
        (Relation.SENT, False),
        (Relation.FRIEND, False),
    ],
)
def test_only_a_day_while_the_pair_is_unconnected_counts(relation, counts):
    assert counts_toward_rest(relation) is counts


def test_a_rested_good_match_is_a_gap_and_stays_on_a_row_with_room():
    row: FreshThenGaps[int] = FreshThenGaps(good=lambda score: score >= 2)

    row.take(3, relation=Relation.NONE, rested=True)
    row.take(2, relation=Relation.NONE, rested=False)
    row.take(1, relation=Relation.NONE, rested=False)

    # The fresh one first; the rested one waits in a gap, best first.
    assert row.row() == (2, 3, 1)


def test_whom_a_row_asks_about_rest():
    """Only a card that could be fresh — a good match, unconnected — needs its
    rest asked: a rest changes nothing for anybody else."""

    row: FreshThenGaps[int] = FreshThenGaps(good=lambda score: score >= 2)

    assert row.may_be_fresh(3, relation=Relation.NONE)
    assert row.may_be_fresh(3, relation=Relation.ASKED_YOU)
    assert not row.may_be_fresh(3, relation=Relation.SENT)
    assert not row.may_be_fresh(3, relation=Relation.FRIEND)
    assert not row.may_be_fresh(1, relation=Relation.NONE)


def test_only_the_two_rows_that_rest_are_reported():
    """New in Raketa turns over by itself and rests nobody (§9.3)."""

    assert {row.value for row in OnScreenRow} == {"SAME_LEVEL", "SAME_VIBE"}
