"""Player reliability in points — the part of ``player_score`` that is a decision
(``docs/adr/0195`` §1, #659).

Everything else this context does is somebody else's fact read through a port.
What is *its own* is here: what each thing on the record costs, the six months it
is remembered for, the order the prices are taken in, the bands and *New*.

**Unit tests over a pure module, and not a duplicate of
``tests/demands/test_player_score_demands.py``.** That suite proves the lines are
read off real streams; this one proves the arithmetic on cases the streams make
slowly — a hundred clamped, a failure six months and a day old, a band's edge.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.engines.matchfit.core import ReliabilityBand, reliability_band_of
from app.kernel import Instant, instant
from app.modules.player_score.domain.points import (
    PRICES,
    START,
    Happened,
    Line,
    PlayerScore,
    ReliabilityCounts,
    remembered_after,
    score_of,
)

#: Wednesday 13 April 2027, 20:00 in Warsaw — six months after Sergio's evening.
NOW = instant(datetime(2027, 4, 13, 18, 0, tzinfo=timezone.utc))


def _days_ago(days: float) -> Instant:
    return instant(NOW - timedelta(days=days))


def _line(happened: Happened, at: Instant | None = None) -> Line:
    return Line(happened=happened, at=at or _days_ago(1))


def _lines(*happened: Happened, from_days_ago: int = 30) -> list[Line]:
    """One line a day, oldest first, in the order given."""

    return [
        _line(one, _days_ago(from_days_ago - index))
        for index, one in enumerate(happened)
    ]


def _points(*happened: Happened) -> int:
    return score_of(_lines(*happened), now=NOW).points


# ---------------------------------------------------------------------------
# The prices
# ---------------------------------------------------------------------------


def test_everyone_starts_at_a_hundred_and_new():
    """Nerea, before anything: 100 · New, and every count at nought."""

    score = score_of([], now=NOW)

    assert score == PlayerScore(
        points=100,
        is_new=True,
        counts=ReliabilityCounts(
            turned_up=0,
            turned_up_of=0,
            late=0,
            kept=0,
            kept_of=0,
            left_in_dispute=0,
        ),
    )
    assert START == 100
    assert score.band is ReliabilityBand.VERY_HIGH


def test_after_her_first_game_she_reads_a_hundred_and_new():
    score = score_of(_lines(Happened.PLAYED_THROUGH, Happened.KEPT), now=NOW)

    assert (score.points, score.band, score.is_new) == (
        100,
        ReliabilityBand.VERY_HIGH,
        True,
    )


@pytest.mark.parametrize(
    ("happened", "price"),
    [
        (Happened.DIDNT_COME, -25),
        (Happened.CAME_LATE, -10),
        (Happened.LEFT_AFTER_THE_CUT_OFF, -15),
        (Happened.CALLED_OFF_BY_LEAVING, -10),
        (Happened.PLAYED_THROUGH, +5),
        (Happened.TURNED_UP_UNCOUNTED, 0),
        (Happened.KEPT, 0),
        (Happened.LEFT_IN_DISPUTE, 0),
    ],
)
def test_each_thing_on_the_record_has_one_price(happened, price):
    """Taken from a figure with room on both sides, so no clamp hides a price."""

    assert PRICES[happened] == price
    start = (Happened.DIDNT_COME, Happened.DIDNT_COME)
    assert _points(*start, happened) == 50 + price


def test_every_thing_the_record_reads_has_a_price():
    assert set(PRICES) == set(Happened)


def test_sergios_autumn():
    """He misses Bonarka (75, High), plays three games through (90, Very high)
    and leaves Kazimierz after the cut-off with nobody taking the seat (75)."""

    missed = _line(Happened.DIDNT_COME, _days_ago(170))
    played = [_line(Happened.PLAYED_THROUGH, _days_ago(160 - day)) for day in range(3)]
    left = _line(Happened.LEFT_AFTER_THE_CUT_OFF, _days_ago(150))

    after_the_miss = score_of([missed], now=NOW)
    after_playing = score_of([missed, *played], now=NOW)
    after_leaving = score_of([missed, *played, left], now=NOW)

    assert (after_the_miss.points, after_the_miss.band) == (75, ReliabilityBand.HIGH)
    assert (after_playing.points, after_playing.band) == (
        90,
        ReliabilityBand.VERY_HIGH,
    )
    assert (after_leaving.points, after_leaving.band) == (75, ReliabilityBand.HIGH)


def test_on_13_april_his_no_show_drops_out():
    """Missed on Wednesday 13 October at 19:00; on 13 April at 20:00 it is six
    months and an hour old, and only what came after it is read."""

    missed = _line(
        Happened.DIDNT_COME, instant(datetime(2026, 10, 13, 17, 0, tzinfo=timezone.utc))
    )
    played = [_line(Happened.PLAYED_THROUGH, _days_ago(160 - day)) for day in range(3)]
    left = _line(Happened.LEFT_AFTER_THE_CUT_OFF, _days_ago(150))

    score = score_of([missed, *played, left], now=NOW)

    assert score.points == 85
    assert score.counts.turned_up_of == 3


# ---------------------------------------------------------------------------
# The clamp, and the order it makes matter
# ---------------------------------------------------------------------------


def test_a_game_played_through_never_takes_the_figure_above_a_hundred():
    assert _points(*[Happened.PLAYED_THROUGH] * 5) == 100


def test_the_figure_never_goes_below_nought_and_climbs_back_from_there():
    assert _points(*[Happened.DIDNT_COME] * 5) == 0
    assert _points(*[Happened.DIDNT_COME] * 5, Happened.PLAYED_THROUGH) == 5


def test_the_prices_are_taken_in_time_order():
    """The clamp makes the order matter: 5 earned at a hundred is nothing."""

    assert _points(Happened.PLAYED_THROUGH, Happened.DIDNT_COME) == 75
    assert _points(Happened.DIDNT_COME, Happened.PLAYED_THROUGH) == 80


def test_the_order_is_the_lines_moments_and_never_the_order_they_arrive_in():
    late = _line(Happened.DIDNT_COME, _days_ago(5))
    early = _line(Happened.PLAYED_THROUGH, _days_ago(9))

    assert score_of([late, early], now=NOW).points == 75


def test_two_lines_at_one_moment_take_the_price_first():
    """A rule for a tie the record can reach — a booked game's hour is both
    its keeping and its turnout — so one record cannot read two figures."""

    at = _days_ago(3)
    lines = [_line(Happened.PLAYED_THROUGH, at), _line(Happened.DIDNT_COME, at)]

    assert score_of(lines, now=NOW).points == 80
    assert score_of(list(reversed(lines)), now=NOW).points == 80


# ---------------------------------------------------------------------------
# Six months
# ---------------------------------------------------------------------------


def test_a_failure_six_months_and_a_day_old_does_not_count():
    old = instant(remembered_after(NOW) - timedelta(days=1))

    assert score_of([_line(Happened.DIDNT_COME, old)], now=NOW).points == 100


def test_a_failure_a_day_short_of_six_months_still_counts():
    recent = instant(remembered_after(NOW) + timedelta(days=1))

    assert score_of([_line(Happened.DIDNT_COME, recent)], now=NOW).points == 75


def test_six_months_is_six_calendar_months():
    assert remembered_after(NOW) == instant(
        datetime(2026, 10, 13, 18, 0, tzinfo=timezone.utc)
    )
    end_of_august = instant(datetime(2027, 8, 31, 12, 0, tzinfo=timezone.utc))
    assert remembered_after(end_of_august) == instant(
        datetime(2027, 2, 28, 12, 0, tzinfo=timezone.utc)
    )


def test_the_window_rolls_one_line_at_a_time():
    """Nothing resets everything at once: the older miss has dropped out, the
    newer one has not."""

    older = _line(
        Happened.DIDNT_COME, instant(remembered_after(NOW) - timedelta(days=2))
    )
    newer = _line(
        Happened.DIDNT_COME, instant(remembered_after(NOW) + timedelta(days=2))
    )

    assert score_of([older, newer], now=NOW).points == 75


# ---------------------------------------------------------------------------
# The bands
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("points", "band"),
    [
        (100, ReliabilityBand.VERY_HIGH),
        (90, ReliabilityBand.VERY_HIGH),
        (89, ReliabilityBand.HIGH),
        (75, ReliabilityBand.HIGH),
        (74, ReliabilityBand.MEDIUM),
        (50, ReliabilityBand.MEDIUM),
        (49, ReliabilityBand.LOW),
        (0, ReliabilityBand.LOW),
    ],
)
def test_the_bands_fall_at_ninety_seventy_five_and_fifty(points, band):
    assert reliability_band_of(points) is band


def test_one_no_show_keeps_you_high_two_close_together_medium_three_low():
    assert score_of(_lines(Happened.DIDNT_COME), now=NOW).band is ReliabilityBand.HIGH
    assert (
        score_of(_lines(*[Happened.DIDNT_COME] * 2), now=NOW).band
        is ReliabilityBand.MEDIUM
    )
    assert (
        score_of(_lines(*[Happened.DIDNT_COME] * 3), now=NOW).band
        is ReliabilityBand.LOW
    )


# ---------------------------------------------------------------------------
# New
# ---------------------------------------------------------------------------


def test_new_until_three_games_are_played_through():
    two = score_of(_lines(*[Happened.PLAYED_THROUGH] * 2), now=NOW)
    three = score_of(_lines(*[Happened.PLAYED_THROUGH] * 3), now=NOW)

    assert two.is_new
    assert not three.is_new


def test_a_game_that_was_not_played_through_never_counts_toward_new():
    score = score_of(
        _lines(
            Happened.CAME_LATE,
            Happened.TURNED_UP_UNCOUNTED,
            Happened.KEPT,
            Happened.PLAYED_THROUGH,
            Happened.PLAYED_THROUGH,
        ),
        now=NOW,
    )

    assert score.is_new


def test_new_is_ever_and_six_months_away_does_not_make_you_new_again():
    long_ago = [
        _line(
            Happened.PLAYED_THROUGH,
            instant(remembered_after(NOW) - timedelta(days=day)),
        )
        for day in (3, 2, 1)
    ]

    score = score_of(long_ago, now=NOW)

    assert not score.is_new
    assert score.counts.turned_up_of == 0


# ---------------------------------------------------------------------------
# The counts
# ---------------------------------------------------------------------------


def test_the_counts_are_read_over_the_same_six_months():
    score = score_of(
        [
            _line(
                Happened.DIDNT_COME, instant(remembered_after(NOW) - timedelta(days=1))
            ),
            *_lines(
                Happened.PLAYED_THROUGH,
                Happened.KEPT,
                Happened.CAME_LATE,
                Happened.KEPT,
                Happened.DIDNT_COME,
                Happened.KEPT,
                Happened.TURNED_UP_UNCOUNTED,
                Happened.KEPT,
                Happened.PLAYED_THROUGH,
                Happened.LEFT_IN_DISPUTE,
                Happened.KEPT,
                Happened.LEFT_AFTER_THE_CUT_OFF,
                Happened.CALLED_OFF_BY_LEAVING,
            ),
        ],
        now=NOW,
    )

    assert score.counts == ReliabilityCounts(
        # Two played through, a late one and one beside somebody who Didn't
        # come — of those and the one they Didn't come to themselves.
        turned_up=4,
        turned_up_of=5,
        late=1,
        kept=5,
        kept_of=7,
        left_in_dispute=1,
    )
