"""Her evenings as ``app/seeds/booked_history.py`` declares them (#573).

What a reader of the fixture would otherwise take on trust: that the endings are
the ones her record is meant to draw, and that her evenings can only land before
her week begins. The database half is ``tests/api/test_seed_booked_history.py``.
"""

from __future__ import annotations

import ast
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from app.kernel import instant
from app.modules.clubs.domain.court_hours import CLUB_ZONE
from app.modules.proposals.domain.deck import week_of
from app.modules.sportsmanship.domain.window import (
    CARD_OPENS_AFTER,
    CARD_STAYS_OPEN_FOR,
)
from app.seeds.booked_history import (
    HER_EVENINGS,
    SETTLED_FOR,
    _plan,
    WHAT_THEY_SAID_ABOUT_HER,
    latest_evening_ends_by,
)
from app.seeds.cohort import (
    COHORT,
    PLAYED_GAMES,
    PROTAGONIST_HANDLE,
    WHAT_PLAYERS_SAID,
)
from app.seeds.sportsmanship import RATED_AFTER

SEEDS = Path(__file__).resolve().parents[2] / "app" / "seeds"

#: The layers the challenge loop writes, which the new path stands without.
OLD_LAYERS = frozenset(
    {
        "games",
        "pool_history",
        "relationships",
        "pairs",
        "paths",
        "plans",
        "loop",
        "rooms",
        "screens",
    }
)
#: The new path's layers, and the population under them.
NEW_PATH = (
    "proposals",
    "bookings",
    "rescues",
    "posts",
    "cohort",
    "booked_history",
    "sportsmanship",
    "payments",
)


def test_her_record_reaches_a_figure_that_is_not_a_full_bar():
    """One evening nobody claimed and one score she never answered, so *shows
    up* and *answers about results* are fractions — and a run of both colours."""

    never = [evening for evening in HER_EVENINGS if not evening.entered]
    unanswered = [
        evening
        for evening in HER_EVENINGS
        if evening.was_scored and not evening.answered
    ]
    played = [evening for evening in HER_EVENINGS if evening.entered]

    assert len(never) == 1
    assert len(unanswered) == 1
    assert {evening.she_won for evening in played} == {True, False}


def test_her_opponents_are_fewer_than_her_counted_games():
    """*Opponent variety* is people over games, so somebody plays her twice."""

    counted = [evening for evening in HER_EVENINGS if evening.was_scored]

    assert len({evening.opponent for evening in counted}) < len(counted)


def test_her_raters_are_cohort_members_she_played_and_nobody_else_rates_her():
    """Her stars are this layer's alone: the cohort's own table no longer names
    her, so one rating is never written twice from two declarations."""

    played = {evening.opponent for evening in HER_EVENINGS if evening.entered}

    assert set(WHAT_THEY_SAID_ABOUT_HER) <= played
    assert PROTAGONIST_HANDLE not in WHAT_PLAYERS_SAID
    for handle in WHAT_THEY_SAID_ABOUT_HER:
        assert COHORT.by_handle(handle)


def test_a_card_is_answered_inside_the_week_it_is_open_for():
    """The day after the evening, whatever day the run falls on: a rating given
    after the card closed is one nobody was shown the card to give."""

    assert CARD_OPENS_AFTER <= RATED_AFTER < CARD_OPENS_AFTER + CARD_STAYS_OPEN_FOR
    # And past the day a silence takes to confirm the newest score, so the
    # court the card is drawn for is settled.
    assert RATED_AFTER > timedelta(hours=24) + timedelta(minutes=10)


@pytest.mark.parametrize("weekday", range(7))
@pytest.mark.parametrize("hour", (0, 8, 23))
def test_the_latest_evening_is_before_her_week_and_long_over(weekday, hour):
    """**Every day of the week**: a booked evening counts toward its week's games
    per week, and every window on it has to have closed by now."""

    monday = datetime(2026, 10, 5, tzinfo=CLUB_ZONE)
    now = instant(monday + timedelta(days=weekday, hours=hour))

    latest = latest_evening_ends_by(now)

    assert week_of(latest - timedelta(minutes=1)) < week_of(now)
    assert latest <= now - SETTLED_FOR


@pytest.mark.parametrize("module", NEW_PATH)
def test_the_new_path_imports_nothing_from_the_old_loop(module):
    """The new loop's layers and the cohort stand on the new path: no challenge,
    no plan, and none of the challenge loop's seed layers."""

    tree = ast.parse((SEEDS / f"{module}.py").read_text())
    imported = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }

    assert not {
        name
        for name in imported
        if name.startswith(("app.modules.challenges", "app.modules.plans"))
        or (name.startswith("app.seeds.") and name.split(".")[2] in OLD_LAYERS)
    }, sorted(imported)


@pytest.mark.parametrize("weekday", range(7))
def test_a_declared_game_keeps_its_day_unless_it_falls_in_her_week(weekday):
    """**A declared game is played on the day it was declared for**, unless that
    day is inside her week — or too recent for every window to have closed —
    when its placement starts from the last day that is not. Her evenings walk
    back one a day from that same day, oldest first."""

    monday = datetime(2026, 10, 5, 19, tzinfo=CLUB_ZONE)
    now = instant(monday + timedelta(days=weekday))
    last_day = (
        (latest_evening_ends_by(now) - timedelta(minutes=1))
        .astimezone(CLUB_ZONE)
        .date()
    )

    planned = _plan(PLAYED_GAMES, now=now)

    declared = [one for one in planned if not one.hers]
    assert [one.game for one in declared] == sorted(
        PLAYED_GAMES, key=lambda game: -game.played_days_ago
    )
    for one in declared:
        assert one.day == min(one.declared, last_day)
        assert one.day < week_of(now) or one.day == last_day
    evenings = [one for one in planned if one.hers]
    assert [one.game for one in evenings] == [
        evening.as_a_game() for evening in HER_EVENINGS
    ]
    assert [one.day for one in evenings] == [
        last_day - timedelta(days=len(HER_EVENINGS) - 1 - index)
        for index in range(len(HER_EVENINGS))
    ]
    assert all(one.day < week_of(now) for one in evenings)
    assert len({one.order for one in planned}) == len(planned)
