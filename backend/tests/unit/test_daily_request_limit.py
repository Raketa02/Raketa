"""The daily limit's day is a Warsaw day (#773; ``docs/adr/0203`` §9; the
rankings mechanics §13.3, PRD #766 call 10): the count of requests to people
outside the requester's groups resets at midnight in Warsaw, never at UTC's."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.kernel import instant
from app.modules.friends.domain.daily_limit import DAILY_REQUEST_LIMIT, day_began


def _utc(*args: int):
    return instant(datetime(*args, tzinfo=timezone.utc))


def test_ten_requests_a_day():
    assert DAILY_REQUEST_LIMIT == 10


def test_a_winter_day_begins_at_23_utc_the_evening_before():
    # 8 November is CET, UTC+1: Warsaw's midnight is 23:00 UTC on the 7th.
    assert day_began(_utc(2026, 11, 8, 9)) == _utc(2026, 11, 7, 23)
    assert day_began(_utc(2026, 11, 7, 23, 30)) == _utc(2026, 11, 7, 23)
    assert day_began(_utc(2026, 11, 7, 22, 59)) == _utc(2026, 11, 6, 23)


def test_a_summer_day_begins_at_22_utc_the_evening_before():
    # 1 July is CEST, UTC+2.
    assert day_began(_utc(2026, 7, 1, 12)) == _utc(2026, 6, 30, 22)


def test_midnight_itself_is_the_new_day():
    midnight = _utc(2026, 11, 7, 23)

    assert day_began(midnight) == midnight
    assert day_began(instant(midnight - timedelta(microseconds=1))) == _utc(
        2026, 11, 6, 23
    )


def test_the_days_either_side_of_a_clock_change_begin_at_their_own_midnight():
    # Clocks go back on 25 October 2026 at 03:00 CEST: that day began at 22:00
    # UTC the evening before, and the next at 23:00 UTC.
    assert day_began(_utc(2026, 10, 25, 12)) == _utc(2026, 10, 24, 22)
    assert day_began(_utc(2026, 10, 26, 12)) == _utc(2026, 10, 25, 23)
