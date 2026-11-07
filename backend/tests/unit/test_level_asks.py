"""**Ask for a level**, at the Friendship's own seam (``docs/adr/0202`` §4; the
mechanics §5; #749): only a friend is asked, once per sport, ever — and the
friend's first level in that sport answers it, once.

Tomek asks Zofia, his friend, to get a padel level from Ogrody's picker.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.kernel import Sport, instant
from app.modules.friends.domain.errors import FriendNotFound, LevelAlreadyAsked
from app.modules.friends.domain.events import LevelAsked, LevelGot
from app.modules.friends.domain.friendship import Friendship, LevelAsk, Where
from app.modules.friends.domain.relation import RequestOrigin
from app.shared.domain import DomainEvent
from app.shared.ids import new_uuid

AT = instant(datetime(2026, 11, 9, 19, tzinfo=timezone.utc))
LATER = instant(AT + timedelta(days=2))
WHERE = Where(made_from=RequestOrigin.MEMBERS)
TOMEK, ZOFIA = new_uuid(), new_uuid()
OGRODY = new_uuid()


def made_friends() -> list[DomainEvent]:
    """Tomek asked, Zofia said yes: the stream so far."""

    friendship = Friendship.between(TOMEK, ZOFIA)
    friendship.ask(requester=TOMEK, where=WHERE, at=AT)
    friendship.accept(by=ZOFIA, at=AT)
    return friendship.pull_events()


def friends() -> Friendship:
    """Replayed, so nothing is pending."""

    return Friendship.from_history(TOMEK, ZOFIA, made_friends())


def asked() -> Friendship:
    friendship = friends()
    friendship.ask_for_a_level(asker=TOMEK, sport=Sport.PADEL, group_id=OGRODY, at=AT)
    return friendship


def test_a_friend_is_asked_for_a_level_in_a_sport():
    assert asked().pull_events() == [
        LevelAsked(
            asker_id=TOMEK,
            friend_id=ZOFIA,
            sport="PADEL",
            group_id=OGRODY,
            occurred_at=AT,
        )
    ]


def test_the_ask_is_kept_on_the_stream():
    friendship = Friendship.from_history(
        TOMEK, ZOFIA, [*made_friends(), *asked().pull_events()]
    )

    # Tomek's, in padel: not Zofia's, and not in any other sport.
    assert friendship.level_asks == (
        LevelAsk(asker_id=TOMEK, sport=Sport.PADEL, group_id=OGRODY, asked_at=AT),
    )


def test_only_a_friend_is_asked():
    strangers = Friendship.between(TOMEK, ZOFIA)
    requested = Friendship.between(TOMEK, ZOFIA)
    requested.ask(requester=TOMEK, where=WHERE, at=AT)

    for not_friends in (strangers, requested):
        with pytest.raises(FriendNotFound):
            not_friends.ask_for_a_level(
                asker=TOMEK, sport=Sport.PADEL, group_id=OGRODY, at=AT
            )


def test_once_per_sport():
    friendship = asked()

    with pytest.raises(LevelAlreadyAsked):
        friendship.ask_for_a_level(
            asker=TOMEK, sport=Sport.PADEL, group_id=OGRODY, at=LATER
        )
    # Another sport is another ask, and the other way round is the other's own.
    friendship.ask_for_a_level(asker=TOMEK, sport=Sport.TENNIS, group_id=OGRODY, at=AT)
    friendship.ask_for_a_level(asker=ZOFIA, sport=Sport.PADEL, group_id=OGRODY, at=AT)


def test_once_ever_even_after_the_friendship_ended_and_was_made_again():
    friendship = asked()
    friendship.remove(by=ZOFIA, at=LATER)
    friendship.ask(requester=ZOFIA, where=WHERE, at=LATER)
    friendship.accept(by=TOMEK, at=LATER)
    again = Friendship.from_history(
        TOMEK, ZOFIA, [*made_friends(), *friendship.pull_events()]
    )

    assert again.are_friends
    with pytest.raises(LevelAlreadyAsked):
        again.ask_for_a_level(asker=TOMEK, sport=Sport.PADEL, group_id=OGRODY, at=LATER)


def test_the_friends_first_level_in_the_sport_answers_the_ask():
    friendship = asked()
    friendship.pull_events()

    friendship.answer_the_ask(friend=ZOFIA, sport=Sport.PADEL, at=LATER)

    assert friendship.pull_events() == [
        LevelGot(
            asker_id=TOMEK,
            friend_id=ZOFIA,
            sport="PADEL",
            group_id=OGRODY,
            occurred_at=LATER,
        )
    ]
    [ask] = friendship.level_asks
    assert ask.got_at == LATER


def test_an_answer_is_recorded_once_and_never_for_what_nobody_asked():
    friendship = asked()
    friendship.answer_the_ask(friend=ZOFIA, sport=Sport.PADEL, at=LATER)
    friendship.pull_events()

    friendship.answer_the_ask(friend=ZOFIA, sport=Sport.PADEL, at=LATER)
    friendship.answer_the_ask(friend=ZOFIA, sport=Sport.TENNIS, at=LATER)
    # Tomek's own level answers nothing: he asked, nobody asked him.
    friendship.answer_the_ask(friend=TOMEK, sport=Sport.PADEL, at=LATER)

    assert friendship.pull_events() == []


def test_a_level_still_answers_an_ask_after_the_friendship_ended():
    """The answer is a fact about the ask; whether anybody is told is
    Notifications' to read — only while they are still friends."""

    friendship = asked()
    friendship.remove(by=TOMEK, at=AT)
    friendship.pull_events()

    friendship.answer_the_ask(friend=ZOFIA, sport=Sport.PADEL, at=LATER)

    assert [type(event) for event in friendship.pull_events()] == [LevelGot]


def test_an_answered_ask_replays_answered():
    friendship = asked()
    friendship.answer_the_ask(friend=ZOFIA, sport=Sport.PADEL, at=LATER)

    again = Friendship.from_history(
        TOMEK, ZOFIA, [*made_friends(), *friendship.pull_events()]
    )

    [ask] = again.level_asks
    assert ask.got_at == LATER
    with pytest.raises(LevelAlreadyAsked):
        again.ask_for_a_level(asker=TOMEK, sport=Sport.PADEL, group_id=OGRODY, at=LATER)
