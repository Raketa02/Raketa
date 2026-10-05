"""*Free for the whole hour* — the one rule a court hour is read against a week by.

A player counts as free for a court hour **only when the whole hour is inside
their weekly hours**, never when merely its start is (the mechanics §4.2,
ADR-0189 §5). The proposer, posting and the rescue board all ask it, so it is
one function in the Player profile's domain and every other context calls it
rather than re-deriving it.

A court hour is an instant — every time is stored in UTC — and a week is wall
clock, so the rule is asked in a zone and the weekday and the hour are read in
it. Start times are the club's own, which is why a half-past start is here: it
needs the two hours it straddles.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.kernel import Zone, instant
from app.modules.player_profile.domain.weekly_hours import (
    WeeklyHours,
    free_for_the_hour,
)

WARSAW = Zone("Europe/Warsaw")


def at(stamp: str) -> datetime:
    """A UTC instant, written as UTC so the zone conversion is the test's."""

    return instant(datetime.fromisoformat(stamp).replace(tzinfo=timezone.utc))


def week(*codes: str) -> WeeklyHours:
    return WeeklyHours.from_codes(codes)


# 2026-09-29 is a Tuesday, and Warsaw is two hours ahead of UTC in September.
TUESDAY_19_00 = at("2026-09-29T17:00:00")
TUESDAY_19_30 = at("2026-09-29T17:30:00")


def test_an_hour_on_the_hour_needs_its_one_cell():
    assert free_for_the_hour(week("2:19"), start=TUESDAY_19_00, zone=WARSAW)
    assert not free_for_the_hour(week("2:18"), start=TUESDAY_19_00, zone=WARSAW)
    assert not free_for_the_hour(week("2:20"), start=TUESDAY_19_00, zone=WARSAW)


def test_the_weekday_and_the_hour_are_read_in_the_zone_and_not_in_utc():
    """17:00 UTC is 19:00 in Warsaw: a week holding Tuesday 17:00 is not free
    for it, and a week holding Monday is not either."""

    assert not free_for_the_hour(week("2:17"), start=TUESDAY_19_00, zone=WARSAW)
    assert not free_for_the_hour(week("1:19"), start=TUESDAY_19_00, zone=WARSAW)


def test_the_offset_follows_the_date_and_not_the_season_it_was_written_in():
    """On 1 December Warsaw is one hour ahead, so 18:00 UTC is 19:00 there."""

    assert free_for_the_hour(week("2:19"), start=at("2026-12-01T18:00:00"), zone=WARSAW)


def test_a_half_past_start_needs_both_hours_it_straddles():
    """Covering the start is not enough: 19:30–20:30 is free only for a week
    holding both 19:00 and 20:00."""

    assert not free_for_the_hour(week("2:19"), start=TUESDAY_19_30, zone=WARSAW)
    assert not free_for_the_hour(week("2:20"), start=TUESDAY_19_30, zone=WARSAW)
    assert free_for_the_hour(week("2:19", "2:20"), start=TUESDAY_19_30, zone=WARSAW)


def test_the_last_hour_of_the_week_ends_at_eleven():
    """22:00–23:00 is the grid's last cell; 22:30 runs past its end, and no week
    can hold the half hour after it."""

    tuesday_22_00 = at("2026-09-29T20:00:00")
    tuesday_22_30 = at("2026-09-29T20:30:00")
    assert free_for_the_hour(week("2:22"), start=tuesday_22_00, zone=WARSAW)
    assert not free_for_the_hour(week("2:22"), start=tuesday_22_30, zone=WARSAW)


@pytest.mark.parametrize("stamp", ["2026-09-29T04:30:00", "2026-09-29T21:00:00"])
def test_an_hour_outside_the_grid_is_never_free(stamp):
    """06:30 and 23:00 in Warsaw: no week holds them, however full it is."""

    every_hour = WeeklyHours.edited(
        (day, hour) for day in range(1, 8) for hour in range(7, 23)
    )
    assert not free_for_the_hour(every_hour, start=at(stamp), zone=WARSAW)


def test_a_blank_week_is_free_for_nothing():
    """A blank week is *absent* for the overlap term (ADR-0102), and a player
    whose week is absent is not free for a court hour: being free is a claim the
    week has to make, and a week that says nothing makes none."""

    assert not free_for_the_hour(WeeklyHours.blank(), start=TUESDAY_19_00, zone=WARSAW)
