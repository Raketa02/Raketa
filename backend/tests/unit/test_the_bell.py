"""**The bell** — when a player last opened their recent notices (#621; the
mechanics Q101, §17.2; the screens A9).

One moment per player, never a read flag per notice: the bell's number is the
notices given since it, so opening the list clears it on every phone at once.
**Opening is idempotent and never moves the moment back** — the same instant
twice records nothing, and neither does an earlier one, which a second process
with a clock behind the first could send.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.kernel import instant
from app.modules.notifications.domain.bell import Bell
from app.modules.notifications.domain.events import RecentNoticesOpened
from app.shared.ids import new_uuid

AT = instant(datetime(2026, 10, 9, 10, tzinfo=timezone.utc))


def a_bell() -> Bell:
    return Bell.from_history(new_uuid(), [])


def test_a_bell_never_opened_has_no_moment():
    assert a_bell().last_opened_at is None


def test_opening_the_list_records_the_moment():
    bell = a_bell()

    opened = bell.open(at=AT)

    assert opened == RecentNoticesOpened(player_id=bell.player_id, occurred_at=AT)
    assert bell.last_opened_at == AT
    assert bell.pull_events() == [opened]


def test_opening_it_again_at_the_same_moment_records_nothing():
    bell = a_bell()
    bell.open(at=AT)
    bell.pull_events()

    assert bell.open(at=AT) is None
    assert bell.pull_events() == []


def test_the_moment_never_moves_back():
    bell = a_bell()
    bell.open(at=AT)
    bell.pull_events()

    assert bell.open(at=AT - timedelta(minutes=1)) is None
    assert bell.last_opened_at == AT
    assert bell.pull_events() == []


def test_a_later_visit_moves_it_on():
    bell = a_bell()
    bell.open(at=AT)

    later = bell.open(at=AT + timedelta(hours=2))

    assert later is not None
    assert bell.last_opened_at == AT + timedelta(hours=2)
    assert bell.version == 2


def test_the_stream_folds_back_into_the_last_visit():
    bell = a_bell()
    bell.open(at=AT)
    bell.open(at=AT + timedelta(hours=2))

    folded = Bell.from_history(bell.player_id, bell.pull_events())

    assert (folded.last_opened_at, folded.version) == (AT + timedelta(hours=2), 2)
