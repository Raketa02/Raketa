"""A court hour is wall clock at the club and an instant everywhere else.

The two places that could be wrong silently: a day read off the UTC instant
instead of the club's clock, and a zone spelled twice that stopped agreeing.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from uuid import uuid4

from app.kernel import instant
from app.modules.clubs.domain.court_hours import CLUB_ZONE, hour_start, local_day
from app.modules.clubs.domain.hours_exceptions import (
    ClosedHours,
    ExceptionReason,
    HoursException,
)
from app.modules.plans.domain.slots import PLATFORM_ZONE


def test_a_club_s_zone_is_the_platform_s_one_locale_assumption():
    """Spelled twice, on purpose — a club's hours are not a plan's — and held
    together here, so the first shard somewhere else moves both."""

    assert CLUB_ZONE.key == PLATFORM_ZONE.key == "Europe/Warsaw"


def test_an_hour_is_its_wall_clock_on_both_sides_of_the_spring_change():
    assert hour_start(date(2026, 3, 28), 9) == datetime(
        2026, 3, 28, 8, tzinfo=timezone.utc
    )
    assert hour_start(date(2026, 3, 29), 9) == datetime(
        2026, 3, 29, 7, tzinfo=timezone.utc
    )


def test_the_day_is_the_club_s_and_not_the_instant_s():
    # 22:30 UTC on Tuesday is already Wednesday in Kraków.
    late = instant(datetime(2026, 10, 6, 22, 30, tzinfo=timezone.utc))

    assert local_day(late) == date(2026, 10, 7)


def test_an_exception_closes_the_hours_of_its_own_days_at_the_club():
    court = uuid4()
    tuesday = HoursException(
        id=uuid4(),
        court_ids=None,
        first_day=date(2026, 10, 6),
        last_day=date(2026, 10, 6),
        hours=ClosedHours(opens=20, closes=23),
        reason=ExceptionReason("Tournament"),
    )

    # 22:00 in Kraków on the Tuesday is 20:00 UTC: closed.
    assert tuesday.covers(court, hour_start(date(2026, 10, 6), 22))
    # 19:00 that Tuesday is before it opens, and Wednesday is another day.
    assert not tuesday.covers(court, hour_start(date(2026, 10, 6), 19))
    assert not tuesday.covers(court, hour_start(date(2026, 10, 7), 20))
