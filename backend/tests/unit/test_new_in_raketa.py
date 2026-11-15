"""*New in Raketa*'s pure rules (#793; the home-rows mechanics §7): who is new,
Warsaw days, the row's order and a See all page. The routes are held in
``tests/api/test_new_in_raketa.py``; this is the edges a clock can't easily
walk to over HTTP."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.kernel import instant
from app.modules.discovery.domain.new_in_raketa import (
    A_PAGE,
    Joiner,
    days_since,
    is_new,
    newest_first,
    on_the_row,
    page_after,
)
from app.modules.discovery.domain.relation import Relation

NOW = instant(datetime(2026, 11, 14, 12, 0, tzinfo=timezone.utc))


def a_joiner(n: int, *, hours_ago: float) -> Joiner:
    return Joiner(
        player_id=UUID(int=n),
        nickname=f"new{n:02d}",
        photo_id=None,
        joined_at=instant(NOW - timedelta(hours=hours_ago)),
    )


def test_new_is_strictly_inside_thirty_days():
    assert is_new(instant(NOW - timedelta(days=30) + timedelta(microseconds=1)), NOW)
    assert not is_new(instant(NOW - timedelta(days=30)), NOW)


def test_days_are_warsaw_days_not_twenty_four_hours():
    # 23:30 Warsaw on the 13th (22:30 UTC) to 00:30 Warsaw on the 14th: a day.
    late = instant(datetime(2026, 11, 13, 22, 30, tzinfo=timezone.utc))
    early = instant(datetime(2026, 11, 13, 23, 30, tzinfo=timezone.utc))
    assert days_since(late, early) == 1
    # 00:30 to 23:30 Warsaw on one day: today.
    morning = instant(datetime(2026, 11, 13, 23, 30, tzinfo=timezone.utc))
    evening = instant(datetime(2026, 11, 14, 22, 30, tzinfo=timezone.utc))
    assert days_since(morning, evening) == 0


def test_the_row_puts_the_unconnected_first_then_sent_then_friends():
    newest = newest_first(a_joiner(n, hours_ago=n) for n in range(1, 7))
    relations = {
        UUID(int=1): Relation.FRIEND,
        UUID(int=2): Relation.SENT,
        UUID(int=3): Relation.ASKED_YOU,
        UUID(int=5): Relation.FRIEND,
    }

    assert [one.nickname for one in on_the_row(newest, relations)] == [
        "new03",
        "new04",
        "new06",
        "new02",
        "new01",
        "new05",
    ]


def test_two_who_joined_at_one_instant_stand_in_one_order():
    one, other = a_joiner(7, hours_ago=1), a_joiner(3, hours_ago=1)

    assert newest_first([one, other]) == newest_first([other, one]) == (other, one)


def test_a_page_is_everybody_behind_the_cursor_as_the_list_stands_now():
    newest = newest_first(a_joiner(n, hours_ago=n) for n in range(1, 46))
    first = page_after(newest, None)
    second = page_after(newest, first.next)
    third = page_after(newest, second.next)

    assert len(first.joiners) == len(second.joiners) == A_PAGE
    assert [len(third.joiners), third.next] == [5, None]
    assert first.joiners + second.joiners + third.joiners == newest

    # A joiner joins between two pages: the next page holds what it held.
    arrived = newest_first([*newest, a_joiner(99, hours_ago=0)])
    assert page_after(arrived, first.next) == second


def test_a_list_of_exactly_one_page_has_no_next():
    newest = newest_first(a_joiner(n, hours_ago=n) for n in range(1, A_PAGE + 1))

    assert page_after(newest, None).next is None
