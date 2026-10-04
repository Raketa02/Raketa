"""Leaving a group, passing it on, editing it and deleting it — on the aggregate
(#506, ``docs/adr/0183`` §7).

The HTTP suite (``tests/api/test_group_members.py`` and
``tests/api/test_group_leaving_and_editing.py``) walks the same stories as a
player meets them; this is each rule itself, read off what the group records.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.modules.groups.domain.errors import (
    GroupHasOtherMembers,
    LoneOwnerCannotLeave,
    NotTheGroupOwner,
)
from app.modules.groups.domain.events import (
    GroupDeleted,
    GroupLeft,
    GroupRenamed,
    JoinPolicyChanged,
    JoinRequestApproved,
    OwnershipPassed,
)
from app.modules.groups.domain.group import Group
from app.modules.groups.domain.value_objects import GroupCode, GroupName, JoinPolicy

NOW = datetime(2026, 9, 25, 18, 0, tzinfo=timezone.utc)
KAROL = uuid4()
EWA = uuid4()
KUBA = uuid4()


def a_group(policy: JoinPolicy = JoinPolicy.ANYONE, *members) -> Group:
    """Karol's group, and whoever joined it after him, a minute apart."""

    group = Group.create_player_group(
        group_id=uuid4(),
        name=GroupName("Kazimierz crew"),
        home_club_id=uuid4(),
        join_policy=policy,
        owner_id=KAROL,
        code=GroupCode("ab3de7fg"),
        occurred_at=NOW,
    )
    for minutes, member in enumerate(members, start=1):
        at = NOW + timedelta(minutes=minutes)
        group.join(member, occurred_at=at)
        if group.is_waiting(member):
            group.approve(member, by=KAROL, occurred_at=at)
    group.pull_events()
    return group


LATER = NOW + timedelta(days=1)


# --------------------------------------------------------------------------- #
# Leaving
# --------------------------------------------------------------------------- #


def test_a_member_who_leaves_is_no_longer_in_it():
    group = a_group(JoinPolicy.ANYONE, EWA, KUBA)

    group.leave(KUBA, occurred_at=LATER)

    [left] = group.pull_events()
    assert left == GroupLeft(group_id=group.id, player_id=KUBA, occurred_at=LATER)
    assert not group.is_member(KUBA)
    assert list(group.members) == [KAROL, EWA]
    assert group.owner_id == KAROL


def test_an_owner_leaving_passes_the_group_to_the_longest_standing_member():
    group = a_group(JoinPolicy.ANYONE, EWA, KUBA)

    group.leave(KAROL, occurred_at=LATER)

    # Ownership passes first, so at no point in the stream is the Owner
    # somebody who is not in the group.
    assert group.pull_events() == [
        OwnershipPassed(group_id=group.id, from_id=KAROL, to_id=EWA, occurred_at=LATER),
        GroupLeft(group_id=group.id, player_id=KAROL, occurred_at=LATER),
    ]
    assert group.owner_id == EWA
    assert list(group.members) == [EWA, KUBA]


def test_longest_standing_is_the_current_stay_so_a_rejoiner_counts_from_again():
    group = a_group(JoinPolicy.ANYONE, EWA, KUBA)
    group.leave(EWA, occurred_at=LATER)
    group.join(EWA, occurred_at=LATER + timedelta(minutes=1))
    group.pull_events()

    group.leave(KAROL, occurred_at=LATER + timedelta(hours=1))

    assert group.owner_id == KUBA


def test_the_queue_passes_with_the_group():
    """Only the Owner answers a request, so the new one finds them waiting."""

    group = a_group(JoinPolicy.PEOPLE_I_APPROVE, EWA)
    asker = uuid4()
    group.join(asker, occurred_at=LATER)

    group.leave(KAROL, occurred_at=LATER)
    group.approve(asker, by=EWA, occurred_at=LATER)

    assert group.is_member(asker)


def test_a_lone_owner_cannot_leave_and_deletes_instead():
    group = a_group()

    with pytest.raises(LoneOwnerCannotLeave):
        group.leave(KAROL, occurred_at=LATER)

    assert group.pull_events() == []
    assert group.is_member(KAROL)


def test_somebody_who_left_may_join_again_under_the_policy_of_the_day():
    group = a_group(JoinPolicy.ANYONE, KUBA)
    group.leave(KUBA, occurred_at=LATER)
    group.change_join_policy(JoinPolicy.PEOPLE_I_APPROVE, by=KAROL, occurred_at=LATER)
    group.pull_events()

    group.join(KUBA, occurred_at=LATER + timedelta(hours=1))

    assert group.is_waiting(KUBA)
    assert not group.is_member(KUBA)


# --------------------------------------------------------------------------- #
# Who can join
# --------------------------------------------------------------------------- #


def test_switching_to_anyone_admits_everybody_waiting_in_the_order_they_asked():
    group = a_group(JoinPolicy.PEOPLE_I_APPROVE, EWA)
    first, second = uuid4(), uuid4()
    group.join(second, occurred_at=LATER)
    group.join(first, occurred_at=LATER + timedelta(minutes=1))
    group.pull_events()

    admitted = group.change_join_policy(
        JoinPolicy.ANYONE, by=KAROL, occurred_at=LATER + timedelta(hours=1)
    )

    at = LATER + timedelta(hours=1)
    # The switch, and then one admission per request it answered — each the
    # Owner letting somebody in, which is what approving already records.
    assert group.pull_events() == [
        JoinPolicyChanged(
            group_id=group.id, join_policy="ANYONE", changed_by=KAROL, occurred_at=at
        ),
        JoinRequestApproved(
            group_id=group.id, player_id=second, approved_by=KAROL, occurred_at=at
        ),
        JoinRequestApproved(
            group_id=group.id, player_id=first, approved_by=KAROL, occurred_at=at
        ),
    ]
    assert admitted == (second, first)
    assert group.join_policy is JoinPolicy.ANYONE
    assert group.waiting == {}
    assert list(group.members) == [KAROL, EWA, second, first]


def test_switching_to_people_i_approve_admits_nobody():
    group = a_group(JoinPolicy.ANYONE, EWA)

    admitted = group.change_join_policy(
        JoinPolicy.PEOPLE_I_APPROVE, by=KAROL, occurred_at=LATER
    )

    assert [type(event) for event in group.pull_events()] == [JoinPolicyChanged]
    assert admitted == ()
    assert group.join_policy is JoinPolicy.PEOPLE_I_APPROVE


def test_saving_the_policy_it_already_has_records_nothing():
    group = a_group(JoinPolicy.PEOPLE_I_APPROVE)
    group.join(KUBA, occurred_at=LATER)
    group.pull_events()

    admitted = group.change_join_policy(
        JoinPolicy.PEOPLE_I_APPROVE, by=KAROL, occurred_at=LATER
    )

    assert group.pull_events() == []
    assert admitted == ()
    assert group.is_waiting(KUBA)


def test_only_the_owner_changes_who_can_join():
    group = a_group(JoinPolicy.PEOPLE_I_APPROVE, EWA)
    group.join(KUBA, occurred_at=LATER)
    group.pull_events()

    with pytest.raises(NotTheGroupOwner):
        group.change_join_policy(JoinPolicy.ANYONE, by=EWA, occurred_at=LATER)

    assert group.pull_events() == []
    assert group.is_waiting(KUBA)


# --------------------------------------------------------------------------- #
# The name
# --------------------------------------------------------------------------- #


def test_the_owner_renames_the_group_and_its_code_stays():
    group = a_group(JoinPolicy.ANYONE, EWA)
    code = group.code

    group.rename(GroupName("  Kazimierz   nights "), by=KAROL, occurred_at=LATER)

    assert group.pull_events() == [
        GroupRenamed(
            group_id=group.id,
            name="Kazimierz nights",
            renamed_by=KAROL,
            occurred_at=LATER,
        )
    ]
    assert group.name == GroupName("Kazimierz nights")
    assert group.code == code


def test_saving_the_name_it_already_has_records_nothing():
    group = a_group()

    group.rename(GroupName("Kazimierz  crew"), by=KAROL, occurred_at=LATER)

    assert group.pull_events() == []


def test_only_the_owner_renames_the_group():
    group = a_group(JoinPolicy.ANYONE, EWA)

    with pytest.raises(NotTheGroupOwner):
        group.rename(GroupName("Ewa's now"), by=EWA, occurred_at=LATER)

    assert group.pull_events() == []


# --------------------------------------------------------------------------- #
# Deleting
# --------------------------------------------------------------------------- #


def test_an_owner_alone_deletes_the_group_and_nobody_is_left_waiting():
    group = a_group(JoinPolicy.PEOPLE_I_APPROVE)
    group.join(KUBA, occurred_at=NOW)
    group.pull_events()

    group.delete(by=KAROL, occurred_at=LATER)

    assert group.pull_events() == [
        GroupDeleted(group_id=group.id, deleted_by=KAROL, occurred_at=LATER)
    ]
    assert group.is_deleted
    assert group.members == {}
    assert group.waiting == {}


def test_a_group_other_people_are_in_cannot_be_deleted():
    group = a_group(JoinPolicy.ANYONE, EWA)

    with pytest.raises(GroupHasOtherMembers):
        group.delete(by=KAROL, occurred_at=LATER)

    assert group.pull_events() == []
    assert not group.is_deleted


def test_only_the_owner_deletes_the_group():
    group = a_group(JoinPolicy.ANYONE, EWA)
    group.leave(KAROL, occurred_at=LATER)
    group.pull_events()

    # Karol has left and Ewa owns it now, alone: only she may delete it.
    with pytest.raises(NotTheGroupOwner):
        group.delete(by=KAROL, occurred_at=LATER)
    group.delete(by=EWA, occurred_at=LATER)

    assert group.is_deleted
