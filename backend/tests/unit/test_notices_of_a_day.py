"""**A player's notices of one day** — the caps and the bundling (#549; the
mechanics §17.2; the screens A7.2).

The seven notices that are always on are given whenever they happen. The three
a player chooses are capped per day in Kraków — *You complete it* once,
*Challenges for you* and *Fill in alerts* three times — and the first two are
**bundled** past their cap: the day's last notice of the kind gathers the rest,
and no phone is pushed again. *Fill in alerts* past theirs are not given at all.
Nothing is given twice about the same thing.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timezone
from uuid import UUID

from app.kernel import Sport, instant
from app.modules.notifications.domain.events import NoticeBundled, NoticeGiven
from app.modules.notifications.domain.notices import (
    Notice,
    NoticeKind,
    NoticesOfADay,
    Opens,
    day_id_for,
)
from app.shared.ids import new_uuid

AT = instant(datetime(2026, 10, 5, 8, tzinfo=timezone.utc))
DAY = date(2026, 10, 5)


def a_day() -> NoticesOfADay:
    return NoticesOfADay.from_history(new_uuid(), DAY, [])


def notice(kind: NoticeKind, *, game: UUID | None = None, key: str | None = None):
    game_id = game or new_uuid()
    return Notice(
        kind=kind,
        key=key or f"{kind}:{game_id}",
        game_id=game_id,
        pool_id=new_uuid(),
        sport=Sport.PADEL,
        game_kind="COMPETITIVE",
        club_id=new_uuid(),
        starts_at=AT,
        opens=Opens.DECK,
    )


def test_a_notice_that_is_always_on_is_given_every_time():
    day = a_day()

    given = [day.give(notice(NoticeKind.SOMEONE_LEFT), at=AT) for _ in range(5)]

    assert all(isinstance(event, NoticeGiven) for event in given)
    assert len(day.pull_events()) == 5


def test_you_complete_it_is_given_once_a_day_and_bundles_the_rest():
    day = a_day()

    first = day.give(notice(NoticeKind.YOU_COMPLETE_IT), at=AT)
    second = day.give(notice(NoticeKind.YOU_COMPLETE_IT), at=AT)
    third = day.give(notice(NoticeKind.YOU_COMPLETE_IT), at=AT)

    assert isinstance(first, NoticeGiven)
    assert isinstance(second, NoticeBundled) and isinstance(third, NoticeBundled)
    assert second.notice_id == third.notice_id == first.notice_id


def test_challenges_are_given_three_times_a_day_then_bundled_into_the_third():
    day = a_day()

    answers = [day.give(notice(NoticeKind.CHALLENGE), at=AT) for _ in range(5)]

    given = [a for a in answers if isinstance(a, NoticeGiven)]
    bundled = [a for a in answers if isinstance(a, NoticeBundled)]
    assert len(given) == 3
    assert {b.notice_id for b in bundled} == {given[-1].notice_id}


def test_fill_in_alerts_past_three_a_day_are_not_given_at_all():
    day = a_day()

    answers = [day.give(notice(NoticeKind.FILL_IN_ALERT), at=AT) for _ in range(4)]

    assert [type(a) for a in answers] == [NoticeGiven] * 3 + [type(None)]
    assert len(day.pull_events()) == 3


def test_the_caps_are_per_kind():
    day = a_day()

    day.give(notice(NoticeKind.YOU_COMPLETE_IT), at=AT)

    assert isinstance(day.give(notice(NoticeKind.CHALLENGE), at=AT), NoticeGiven)
    assert isinstance(day.give(notice(NoticeKind.FILL_IN_ALERT), at=AT), NoticeGiven)


def test_nothing_is_given_twice_about_the_same_thing():
    day = a_day()
    game = new_uuid()

    first = day.give(notice(NoticeKind.CHALLENGE, game=game), at=AT)
    again = day.give(notice(NoticeKind.CHALLENGE, game=game), at=AT)
    day.give(notice(NoticeKind.YOU_COMPLETE_IT), at=AT)
    bundled = day.give(notice(NoticeKind.YOU_COMPLETE_IT, game=game), at=AT)
    bundled_again = day.give(notice(NoticeKind.YOU_COMPLETE_IT, game=game), at=AT)

    assert isinstance(first, NoticeGiven)
    assert again is None
    assert isinstance(bundled, NoticeBundled)
    assert bundled_again is None


def test_a_notice_of_the_player_s_own_act_is_given_as_their_own():
    """Born seen (the mechanics Q102): listed, and never counted or pushed."""

    day = a_day()

    own = day.give(replace(notice(NoticeKind.GAME_BOOKED), own=True), at=AT)
    theirs = day.give(notice(NoticeKind.GAME_BOOKED), at=AT)

    assert isinstance(own, NoticeGiven) and own.own is True
    assert isinstance(theirs, NoticeGiven) and theirs.own is False


def test_a_stream_folds_back_to_its_count():
    day = a_day()
    day.give(notice(NoticeKind.YOU_COMPLETE_IT), at=AT)

    again = NoticesOfADay.from_history(day.player_id, DAY, day.pull_events())

    assert again.version == 1
    assert isinstance(
        again.give(notice(NoticeKind.YOU_COMPLETE_IT), at=AT), NoticeBundled
    )


def test_a_day_is_one_stream_per_player():
    player = new_uuid()

    assert day_id_for(player, DAY) == day_id_for(player, DAY)
    assert day_id_for(player, DAY) != day_id_for(player, date(2026, 10, 6))
    assert day_id_for(player, DAY) != day_id_for(new_uuid(), DAY)
