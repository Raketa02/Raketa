"""A *People I approve* group's Join requests, on the aggregate (#505,
``docs/adr/0183`` §7).

The HTTP suite (``tests/api/test_join_requests.py``) walks the same story as a
player meets it; this is the rule itself, read off what the group records.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.modules.groups.domain.errors import JoinRequestNotFound, NotTheGroupOwner
from app.modules.groups.domain.events import (
    GroupJoined,
    JoinRequestApproved,
    JoinRequestDeclined,
    JoinRequested,
    JoinRequestWithdrawn,
)
from app.modules.groups.domain.group import Group
from app.modules.groups.domain.value_objects import GroupCode, GroupName, JoinPolicy

NOW = datetime(2026, 9, 25, 18, 0, tzinfo=timezone.utc)
KAROL = uuid4()
KASIA = uuid4()


def a_group(policy: JoinPolicy = JoinPolicy.PEOPLE_I_APPROVE) -> Group:
    group = Group.create_player_group(
        group_id=uuid4(),
        name=GroupName("Ogrody wieczorem"),
        home_club_id=uuid4(),
        join_policy=policy,
        owner_id=KAROL,
        code=GroupCode("ab3de7fg"),
        occurred_at=NOW,
    )
    group.pull_events()
    return group


def test_asking_to_join_a_group_that_needs_approval_leaves_a_request_waiting():
    group = a_group()

    group.join(KASIA, occurred_at=NOW)

    assert [type(event) for event in group.pull_events()] == [JoinRequested]
    assert group.is_waiting(KASIA)
    assert not group.is_member(KASIA)


def test_asking_again_while_waiting_records_nothing():
    group = a_group()
    group.join(KASIA, occurred_at=NOW)
    group.pull_events()

    group.join(KASIA, occurred_at=NOW + timedelta(minutes=5))

    assert group.pull_events() == []


def test_under_anyone_the_same_tap_admits_at_once():
    group = a_group(JoinPolicy.ANYONE)

    group.join(KASIA, occurred_at=NOW)

    assert [type(event) for event in group.pull_events()] == [GroupJoined]
    assert group.is_member(KASIA)


def test_approving_is_admitting_in_one_event():
    group = a_group()
    group.join(KASIA, occurred_at=NOW)
    group.pull_events()

    group.approve(KASIA, by=KAROL, occurred_at=NOW + timedelta(hours=1))

    [approved] = group.pull_events()
    assert approved == JoinRequestApproved(
        group_id=group.id,
        player_id=KASIA,
        approved_by=KAROL,
        occurred_at=NOW + timedelta(hours=1),
    )
    assert group.is_member(KASIA)
    assert not group.is_waiting(KASIA)
    # Joined last, so last in the order *the first to join* is read from.
    assert list(group.members) == [KAROL, KASIA]


def test_approving_a_member_records_nothing():
    group = a_group()
    group.join(KASIA, occurred_at=NOW)
    group.approve(KASIA, by=KAROL, occurred_at=NOW)
    group.pull_events()

    group.approve(KASIA, by=KAROL, occurred_at=NOW)

    assert group.pull_events() == []


def test_nobody_is_admitted_who_did_not_ask():
    group = a_group()

    with pytest.raises(JoinRequestNotFound):
        group.approve(KASIA, by=KAROL, occurred_at=NOW)
    assert group.pull_events() == []


def test_declining_removes_the_request_and_they_may_ask_again():
    group = a_group()
    group.join(KASIA, occurred_at=NOW)
    group.pull_events()

    group.decline(KASIA, by=KAROL, occurred_at=NOW)
    declined = group.pull_events()
    group.join(KASIA, occurred_at=NOW + timedelta(days=1))

    assert [type(event) for event in declined] == [JoinRequestDeclined]
    assert [type(event) for event in group.pull_events()] == [JoinRequested]
    assert group.is_waiting(KASIA)


def test_declining_what_is_not_waiting_records_nothing_and_removes_no_member():
    group = a_group()
    group.join(KASIA, occurred_at=NOW)
    group.approve(KASIA, by=KAROL, occurred_at=NOW)
    group.pull_events()

    group.decline(KASIA, by=KAROL, occurred_at=NOW)

    assert group.pull_events() == []
    assert group.is_member(KASIA)


@pytest.mark.parametrize("answer", ["approve", "decline"])
def test_nobody_but_the_owner_answers(answer):
    group = a_group()
    group.join(KASIA, occurred_at=NOW)
    group.pull_events()

    with pytest.raises(NotTheGroupOwner):
        getattr(group, answer)(KASIA, by=uuid4(), occurred_at=NOW)
    assert group.pull_events() == []
    assert group.is_waiting(KASIA)


def test_a_request_s_life_replays_to_the_group_it_left():
    """Created, asked, declined, asked again, approved — and the stream folds
    back to a group with her in it and nobody waiting."""

    group = Group.create_player_group(
        group_id=uuid4(),
        name=GroupName("Ogrody wieczorem"),
        home_club_id=uuid4(),
        join_policy=JoinPolicy.PEOPLE_I_APPROVE,
        owner_id=KAROL,
        code=GroupCode("ab3de7fg"),
        occurred_at=NOW,
    )
    group.join(KASIA, occurred_at=NOW)
    group.decline(KASIA, by=KAROL, occurred_at=NOW)
    group.join(KASIA, occurred_at=NOW)
    group.approve(KASIA, by=KAROL, occurred_at=NOW)

    replayed = Group.from_history(group.pull_events())

    assert replayed.waiting == {}
    assert list(replayed.members) == [KAROL, KASIA]
    assert replayed.version == 5


# --------------------------------------------------------------------------- #
# Withdrawing one (#792, docs/adr/0204 §11)
# --------------------------------------------------------------------------- #


def test_the_asker_withdraws_and_nothing_waits_any_more():
    group = a_group()
    group.join(KASIA, occurred_at=NOW)
    group.pull_events()

    group.withdraw_request(KASIA, occurred_at=NOW + timedelta(minutes=2))

    [withdrawn] = group.pull_events()
    assert withdrawn == JoinRequestWithdrawn(
        group_id=group.id, player_id=KASIA, occurred_at=NOW + timedelta(minutes=2)
    )
    assert not group.is_waiting(KASIA)
    assert not group.is_member(KASIA)


def test_withdrawing_again_records_nothing():
    group = a_group()
    group.join(KASIA, occurred_at=NOW)
    group.withdraw_request(KASIA, occurred_at=NOW)
    group.pull_events()

    group.withdraw_request(KASIA, occurred_at=NOW)

    assert group.pull_events() == []


def test_withdrawing_a_request_approved_a_moment_earlier_leaves_her_a_member():
    group = a_group()
    group.join(KASIA, occurred_at=NOW)
    group.approve(KASIA, by=KAROL, occurred_at=NOW)
    group.pull_events()

    group.withdraw_request(KASIA, occurred_at=NOW + timedelta(seconds=5))

    assert group.pull_events() == []
    assert group.is_member(KASIA)


def test_withdrawing_a_declined_request_records_nothing():
    group = a_group()
    group.join(KASIA, occurred_at=NOW)
    group.decline(KASIA, by=KAROL, occurred_at=NOW)
    group.pull_events()

    group.withdraw_request(KASIA, occurred_at=NOW)

    assert group.pull_events() == []


def test_after_withdrawing_she_may_ask_again_and_the_stream_replays():
    group = a_group()
    group.join(KASIA, occurred_at=NOW)
    group.withdraw_request(KASIA, occurred_at=NOW)
    group.join(KASIA, occurred_at=NOW + timedelta(days=1))

    assert group.is_waiting(KASIA)
    replayed = Group.from_history(
        [
            *Group.create_player_group(
                group_id=group.id,
                name=GroupName("Ogrody wieczorem"),
                home_club_id=group.home_club_id,
                join_policy=JoinPolicy.PEOPLE_I_APPROVE,
                owner_id=KAROL,
                code=GroupCode("ab3de7fg"),
                occurred_at=NOW,
            ).pull_events(),
            *group.pull_events(),
        ]
    )
    assert list(replayed.waiting) == [KASIA]
    assert replayed.version == 4
