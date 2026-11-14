"""The Friendship aggregate's rules, at its own seam (``docs/adr/0202`` §1–§2;
#745): at most one thing stands between two players, a second request crosses
the first, and taking back nothing records nothing."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.kernel import InvariantViolated, Sport, instant
from app.modules.friends.domain.errors import (
    AlreadyFriends,
    CannotBefriendYourself,
    FriendRequestAlreadySent,
    FriendRequestNotFound,
)
from app.modules.friends.domain.events import (
    FriendRequestCrossed,
    FriendRequested,
    FriendshipEnded,
    FriendsMade,
)
from app.modules.friends.domain.friendship import Friendship, Where
from app.modules.friends.domain.ids import friendship_id
from app.modules.friends.domain.relation import FriendRelation, RequestOrigin
from app.shared.ids import new_uuid

AT = instant(datetime(2026, 11, 6, 9, tzinfo=timezone.utc))
WHERE = Where(made_from=RequestOrigin.MEMBERS)
INES, TOMEK = new_uuid(), new_uuid()


def asked() -> Friendship:
    friendship = Friendship.between(INES, TOMEK)
    friendship.ask(requester=INES, where=WHERE, at=AT)
    return friendship


def replayed(friendship: Friendship) -> Friendship:
    return Friendship.from_history(INES, TOMEK, friendship.pull_events())


def test_one_stream_whichever_way_round():
    assert friendship_id(INES, TOMEK) == friendship_id(TOMEK, INES)
    assert Friendship.between(TOMEK, INES).id == Friendship.between(INES, TOMEK).id


def test_nobody_befriends_themselves():
    with pytest.raises(CannotBefriendYourself):
        Friendship.between(INES, INES)


def test_a_request_reads_sent_and_asked_you():
    friendship = replayed(asked())

    assert friendship.relation_of(INES) is FriendRelation.SENT
    assert friendship.relation_of(TOMEK) is FriendRelation.ASKED_YOU


def test_nobody_asks_twice_and_not_now_keeps_it_open():
    friendship = asked()
    friendship.set_aside(by=TOMEK, at=AT)
    friendship.set_aside(by=TOMEK, at=AT)

    with pytest.raises(FriendRequestAlreadySent):
        friendship.ask(requester=INES, where=WHERE, at=AT)
    assert len(friendship.pull_events()) == 2
    assert friendship.request is not None and friendship.request.set_aside


def test_a_second_request_crosses_the_first():
    friendship = asked()

    relation = friendship.ask(requester=TOMEK, where=WHERE, at=AT)

    assert relation is FriendRelation.FRIEND
    events = friendship.pull_events()
    assert [type(event) for event in events] == [
        FriendRequested,
        FriendRequestCrossed,
        FriendsMade,
    ]
    made = events[-1]
    assert isinstance(made, FriendsMade)
    assert (made.requester_id, made.addressee_id, made.how) == (
        INES,
        TOMEK,
        "CROSSED",
    )
    with pytest.raises(AlreadyFriends):
        friendship.ask(requester=INES, where=WHERE, at=AT)


def test_only_the_person_asked_answers():
    friendship = asked()

    with pytest.raises(FriendRequestNotFound):
        friendship.accept(by=INES, at=AT)
    with pytest.raises(FriendRequestNotFound):
        friendship.set_aside(by=INES, at=AT)


def test_cancelling_or_removing_nothing_records_nothing():
    friendship = Friendship.between(INES, TOMEK)

    friendship.cancel(by=INES, at=AT)
    friendship.remove(by=INES, at=AT)
    friendship.end_by_a_block(blocker=INES, at=AT)

    assert friendship.pull_events() == []


def test_only_the_requester_cancels():
    friendship = asked()
    friendship.pull_events()

    friendship.cancel(by=TOMEK, at=AT)

    assert friendship.pull_events() == []
    assert friendship.relation_of(TOMEK) is FriendRelation.ASKED_YOU


def test_a_block_ends_an_open_request_as_well_as_a_friendship():
    open_request = asked()
    open_request.end_by_a_block(blocker=TOMEK, at=AT)
    friends = asked()
    friends.accept(by=TOMEK, at=AT)
    friends.end_by_a_block(blocker=INES, at=AT)

    for friendship in (open_request, friends):
        ended = friendship.pull_events()[-1]
        assert isinstance(ended, FriendshipEnded)
        assert ended.how == "BLOCKED"
        assert friendship.relation_of(INES) is FriendRelation.NONE
        assert friendship.relation_of(TOMEK) is FriendRelation.NONE


def test_a_request_the_addressee_never_sees_reads_none_from_their_side():
    friendship = Friendship.between(INES, TOMEK)
    friendship.ask(requester=INES, where=WHERE, at=AT, unseen=True)
    friendship = replayed(friendship)

    assert friendship.relation_of(INES) is FriendRelation.SENT
    assert friendship.relation_of(TOMEK) is FriendRelation.NONE
    with pytest.raises(FriendRequestNotFound):
        friendship.accept(by=TOMEK, at=AT)
    with pytest.raises(FriendRequestAlreadySent):
        friendship.ask(requester=INES, where=WHERE, at=AT)


def test_a_links_request_names_no_group_or_sport():
    with pytest.raises(InvariantViolated):
        Where(made_from=RequestOrigin.LINK, sport=Sport.PADEL)


def test_a_same_vibe_request_names_no_group_or_sport():
    """*6 things in common* names neither (#795): a screen sending either has
    both dropped where the request is read, never refused."""

    with pytest.raises(InvariantViolated):
        Where(made_from=RequestOrigin.SAME_VIBE, sport=Sport.PADEL)
    with pytest.raises(InvariantViolated):
        Where(made_from=RequestOrigin.SAME_VIBE, group_id=new_uuid())

    assert Where.pressed_on(
        RequestOrigin.SAME_VIBE, group_id=new_uuid(), sport=Sport.PADEL
    ) == Where(made_from=RequestOrigin.SAME_VIBE)


# --------------------------------------------------------------------------- #
# From the ranking, and the daily limit (#773; docs/adr/0203 §9)
# --------------------------------------------------------------------------- #

RANKING = Where(made_from=RequestOrigin.RANKING, sport=Sport.PADEL)


def test_a_rankings_request_names_its_sport_and_no_group():
    assert RANKING.sport is Sport.PADEL
    with pytest.raises(InvariantViolated):
        Where(made_from=RequestOrigin.RANKING)
    with pytest.raises(InvariantViolated):
        Where(made_from=RequestOrigin.RANKING, group_id=new_uuid(), sport=Sport.PADEL)


def test_a_request_is_never_counted_and_nothing_limits_how_many():
    """``docs/adr/0204`` §2: the daily limit went, so a request records no
    count — the field is decoded from older rows and never written true."""

    for addressee in (new_uuid() for _ in range(50)):
        friendship = Friendship.between(INES, addressee)
        friendship.ask(requester=INES, where=RANKING, at=AT)

        (requested,) = friendship.pull_events()
        assert isinstance(requested, FriendRequested)
        assert requested.counted is False
        assert requested.made_from == "RANKING"


def test_a_request_once_counted_replays_as_any_request():
    """A stored ``friend_requested`` from before #791 may carry ``counted``
    true; it folds as any request."""

    friendship = Friendship.from_history(
        INES,
        TOMEK,
        [
            FriendRequested(
                requester_id=INES,
                addressee_id=TOMEK,
                made_from="RANKING",
                group_id=None,
                sport="PADEL",
                occurred_at=AT,
                counted=True,
            )
        ],
    )

    assert friendship.relation_of(TOMEK) is FriendRelation.ASKED_YOU
    assert friendship.request is not None
    assert friendship.request.where == RANKING


def test_a_rankings_screen_drops_the_group_a_client_sent():
    """The Rankings page shows no group, so a group sent with it is dropped
    where the request is read — never refused (#773)."""

    where = Where.pressed_on(
        RequestOrigin.RANKING, group_id=new_uuid(), sport=Sport.PADEL
    )
    members = Where.pressed_on(
        RequestOrigin.MEMBERS, group_id=(group := new_uuid()), sport=Sport.PADEL
    )

    assert where == RANKING
    assert members.group_id == group
