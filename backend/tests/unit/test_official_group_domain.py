"""An official group, on the aggregate (#509, ``docs/adr/0183`` §3, §7).

Marta runs *Ogrody 33 Club* for her club's 48-person padel WhatsApp group. It
has **no Owner**: she is its Administrator, and running it is not membership.
Only she answers its requests and edits it; Tomek, who runs it and plays, joins
it directly. The HTTP suite (``tests/api/test_official_groups.py``) walks the
same stories as an administrator and a player meet them; this is each rule
itself, read off what the group records.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.kernel import InvariantViolated, Sport
from app.modules.groups.domain.errors import (
    GroupSportsRequired,
    NotTheGroupOwner,
    SportNotOfferedByClub,
    WhatsAppSizeInvalid,
)
from app.modules.groups.domain.events import (
    AdministratorAssigned,
    GroupJoined,
    GroupLeft,
    GroupRenamed,
    JoinPolicyChanged,
    JoinRequestApproved,
    JoinRequestDeclined,
    JoinRequested,
    OfficialGroupCreated,
    SportsDeclared,
    WhatsAppSizeSet,
)
from app.modules.groups.domain.group import Group
from app.modules.groups.domain.value_objects import (
    DeclaredSports,
    GroupCode,
    GroupKind,
    GroupName,
    JoinPolicy,
    WhatsAppSize,
)

NOW = datetime(2026, 9, 26, 18, 0, tzinfo=timezone.utc)
LATER = NOW + timedelta(hours=1)
CLUB = uuid4()
#: Marta's administratorship at the club, and the account she signs in with.
MARTA = uuid4()
MARTA_ACCOUNT = uuid4()
#: A colleague's administratorship at the same club.
OLA = uuid4()
OLA_ACCOUNT = uuid4()
#: The club account at the desk, which hands a group over.
DESK = uuid4()
MICHAL = uuid4()
KASIA = uuid4()


def ogrody_33_club(policy: JoinPolicy = JoinPolicy.PEOPLE_I_APPROVE) -> Group:
    group = Group.create_official_group(
        group_id=uuid4(),
        name=GroupName("Ogrody 33 Club"),
        club_id=CLUB,
        join_policy=policy,
        administrator_id=MARTA,
        created_by=MARTA_ACCOUNT,
        whatsapp_size=WhatsAppSize(48),
        sports=DeclaredSports.of([Sport.PADEL]),
        code=GroupCode("ab3de7fg"),
        occurred_at=NOW,
    )
    group.pull_events()
    return group


def answered_by_marta(**kwargs) -> dict:
    return {"by": MARTA_ACCOUNT, "as_administrator": MARTA, **kwargs}


# --------------------------------------------------------------------------- #
# What an official group is
# --------------------------------------------------------------------------- #


def test_it_is_created_by_its_administrator_and_has_no_owner_and_nobody_in_it():
    group = Group.create_official_group(
        group_id=uuid4(),
        name=GroupName("Ogrody 33 Club"),
        club_id=CLUB,
        join_policy=JoinPolicy.PEOPLE_I_APPROVE,
        administrator_id=MARTA,
        created_by=MARTA_ACCOUNT,
        whatsapp_size=WhatsAppSize(48),
        sports=DeclaredSports.of([Sport.TENNIS, Sport.PADEL]),
        code=GroupCode("ab3de7fg"),
        occurred_at=NOW,
    )

    (created,) = group.pull_events()
    assert isinstance(created, OfficialGroupCreated)
    assert created.administrator_id == MARTA
    assert created.created_by == MARTA_ACCOUNT
    assert created.home_club_id == CLUB
    assert created.whatsapp_size == 48
    # In the registry's order, never the order they were ticked in.
    assert created.sports == ("PADEL", "TENNIS")
    assert group.kind is GroupKind.OFFICIAL
    assert group.owner_id is None
    assert group.administrator_id == MARTA
    # Running an official group is not membership (docs/adr/0183 §7).
    assert group.members == {}
    assert group.whatsapp_size == WhatsAppSize(48)
    assert group.declared_sports == DeclaredSports.of([Sport.PADEL, Sport.TENNIS])


def test_a_player_group_is_of_the_player_kind():
    group = Group.create_player_group(
        group_id=uuid4(),
        name=GroupName("Kazimierz crew"),
        home_club_id=CLUB,
        join_policy=JoinPolicy.ANYONE,
        owner_id=MICHAL,
        code=GroupCode("ab3de7fg"),
        occurred_at=NOW,
    )

    assert group.kind is GroupKind.PLAYER
    assert group.administrator_id is None
    assert group.whatsapp_size is None
    assert group.declared_sports is None


def test_the_stream_folds_back_into_the_same_group():
    group = ogrody_33_club()
    group.join(MICHAL, occurred_at=LATER)
    group.approve(MICHAL, occurred_at=LATER, **answered_by_marta())
    group.set_whatsapp_size(WhatsAppSize(52), occurred_at=LATER, **answered_by_marta())
    group.declare_sports(
        DeclaredSports.of([Sport.PADEL, Sport.SQUASH]),
        occurred_at=LATER,
        **answered_by_marta(),
    )
    created = Group.create_official_group(
        group_id=group.id,
        name=GroupName("Ogrody 33 Club"),
        club_id=CLUB,
        join_policy=JoinPolicy.PEOPLE_I_APPROVE,
        administrator_id=MARTA,
        created_by=MARTA_ACCOUNT,
        whatsapp_size=WhatsAppSize(48),
        sports=DeclaredSports.of([Sport.PADEL]),
        code=GroupCode("ab3de7fg"),
        occurred_at=NOW,
    ).pull_events()

    replayed = Group.from_history([*created, *group.pull_events()])

    assert replayed.kind is GroupKind.OFFICIAL
    assert replayed.owner_id is None
    assert replayed.administrator_id == MARTA
    assert replayed.members == {MICHAL: LATER}
    assert replayed.whatsapp_size == WhatsAppSize(52)
    assert replayed.declared_sports == DeclaredSports.of([Sport.PADEL, Sport.SQUASH])
    assert replayed.version == 5


# --------------------------------------------------------------------------- #
# The WhatsApp group size and the declared sports
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("size", [2, 48, 1024])
def test_a_whatsapp_size_is_a_whole_number_from_two_to_1024(size):
    assert WhatsAppSize(size).value == size


@pytest.mark.parametrize(
    ("players", "size", "percent"),
    [
        (11, 48, 23),
        (38, 48, 79),
        (8, 30, 27),
        # A half is rounded up.
        (1, 8, 13),
        (0, 48, 0),
        (48, 48, 100),
        # Never capped: the club sees the real figure.
        (52, 48, 108),
        (3, 2, 150),
    ],
)
def test_the_club_s_from_whatsapp_figure_is_a_whole_percent(players, size, percent):
    assert WhatsAppSize(size).percent_arrived(players) == percent


@pytest.mark.parametrize("size", [-1, 0, 1, 1025, True, 48.0])
def test_a_whatsapp_size_outside_that_is_refused_under_its_field(size):
    with pytest.raises(WhatsAppSizeInvalid) as refused:
        WhatsAppSize(size)

    assert refused.value.details == {"field": "whatsapp_size"}


def test_declared_sports_are_required():
    with pytest.raises(GroupSportsRequired) as refused:
        DeclaredSports.of([])

    assert refused.value.details == {"field": "sports"}


def test_declared_sports_are_a_subset_of_the_club_s_and_the_refusal_names_the_sport():
    offered = (Sport.PADEL, Sport.TENNIS)

    assert DeclaredSports.at_club(
        [Sport.TENNIS], offered=offered
    ).in_registry_order() == (Sport.TENNIS,)
    with pytest.raises(SportNotOfferedByClub) as refused:
        DeclaredSports.at_club([Sport.PADEL, Sport.SQUASH], offered=offered)

    assert refused.value.details == {"field": "sports", "sport": "SQUASH"}


def test_an_empty_list_is_refused_as_required_before_anything_is_compared():
    with pytest.raises(GroupSportsRequired):
        DeclaredSports.at_club([], offered=(Sport.PADEL,))


# --------------------------------------------------------------------------- #
# Who gets in
# --------------------------------------------------------------------------- #


def test_under_people_i_approve_a_player_s_tap_is_a_join_request():
    group = ogrody_33_club()

    group.join(MICHAL, occurred_at=LATER)

    (asked,) = group.pull_events()
    assert isinstance(asked, JoinRequested)
    assert group.is_waiting(MICHAL)


def test_the_account_that_runs_it_joins_directly_even_under_people_i_approve():
    group = ogrody_33_club()

    group.join(MARTA_ACCOUNT, occurred_at=LATER, runs_it=True)

    (joined,) = group.pull_events()
    assert isinstance(joined, GroupJoined)
    assert group.is_member(MARTA_ACCOUNT)


def test_the_account_that_runs_it_and_had_asked_before_is_let_in_by_its_own_tap():
    """Asked as a player before the club made them its administrator: they would
    otherwise be asking themselves (``docs/adr/0183`` §7)."""

    group = ogrody_33_club()
    group.join(MARTA_ACCOUNT, occurred_at=NOW)
    group.pull_events()

    group.join(MARTA_ACCOUNT, occurred_at=LATER, runs_it=True)

    (admitted,) = group.pull_events()
    assert isinstance(admitted, JoinRequestApproved)
    assert admitted.approved_by == MARTA_ACCOUNT
    assert group.is_member(MARTA_ACCOUNT)


def test_running_a_player_group_is_no_such_thing():
    group = Group.create_player_group(
        group_id=uuid4(),
        name=GroupName("Kazimierz crew"),
        home_club_id=CLUB,
        join_policy=JoinPolicy.PEOPLE_I_APPROVE,
        owner_id=MICHAL,
        code=GroupCode("ab3de7fg"),
        occurred_at=NOW,
    )

    with pytest.raises(InvariantViolated):
        group.join(KASIA, occurred_at=LATER, runs_it=True)


def test_its_administrator_approves_and_declines():
    group = ogrody_33_club()
    group.join(MICHAL, occurred_at=NOW)
    group.join(KASIA, occurred_at=NOW)
    group.pull_events()

    group.approve(MICHAL, occurred_at=LATER, **answered_by_marta())
    group.decline(KASIA, occurred_at=LATER, **answered_by_marta())

    approved, declined = group.pull_events()
    assert isinstance(approved, JoinRequestApproved)
    assert approved.approved_by == MARTA_ACCOUNT
    assert isinstance(declined, JoinRequestDeclined)
    assert declined.declined_by == MARTA_ACCOUNT
    assert group.is_member(MICHAL)
    assert not group.is_waiting(KASIA)


@pytest.mark.parametrize(
    "act",
    [
        lambda group, **by: group.approve(MICHAL, occurred_at=LATER, **by),
        lambda group, **by: group.decline(MICHAL, occurred_at=LATER, **by),
        lambda group, **by: group.rename(
            GroupName("Ogrody nights"), occurred_at=LATER, **by
        ),
        lambda group, **by: group.change_join_policy(
            JoinPolicy.ANYONE, occurred_at=LATER, **by
        ),
        lambda group, **by: group.set_whatsapp_size(
            WhatsAppSize(52), occurred_at=LATER, **by
        ),
        lambda group, **by: group.declare_sports(
            DeclaredSports.of([Sport.TENNIS]), occurred_at=LATER, **by
        ),
    ],
    ids=["approve", "decline", "rename", "policy", "size", "sports"],
)
@pytest.mark.parametrize(
    "who",
    [
        {"by": MICHAL},
        {"by": MARTA_ACCOUNT},
        {"by": uuid4(), "as_administrator": OLA},
    ],
    ids=["a member", "marta-as-a-player", "a-colleague"],
)
def test_nobody_but_its_administrator_answers_or_edits_it(act, who):
    group = ogrody_33_club()
    group.join(MICHAL, occurred_at=NOW)
    group.pull_events()

    with pytest.raises(NotTheGroupOwner):
        act(group, **who)

    assert group.pull_events() == []


# --------------------------------------------------------------------------- #
# Settings
# --------------------------------------------------------------------------- #


def test_the_whatsapp_size_changes_and_saving_the_same_records_nothing():
    group = ogrody_33_club()

    group.set_whatsapp_size(WhatsAppSize(52), occurred_at=LATER, **answered_by_marta())
    group.set_whatsapp_size(WhatsAppSize(52), occurred_at=LATER, **answered_by_marta())

    (changed,) = group.pull_events()
    assert changed == WhatsAppSizeSet(
        group_id=group.id, whatsapp_size=52, set_by=MARTA_ACCOUNT, occurred_at=LATER
    )


def test_the_sports_are_declared_again_and_saving_the_same_records_nothing():
    group = ogrody_33_club()
    both = DeclaredSports.of([Sport.TENNIS, Sport.PADEL])

    group.declare_sports(both, occurred_at=LATER, **answered_by_marta())
    group.declare_sports(both, occurred_at=LATER, **answered_by_marta())

    (declared,) = group.pull_events()
    assert declared == SportsDeclared(
        group_id=group.id,
        sports=("PADEL", "TENNIS"),
        declared_by=MARTA_ACCOUNT,
        occurred_at=LATER,
    )


def test_its_administrator_renames_it_and_anyone_admits_everybody_waiting():
    group = ogrody_33_club()
    group.join(MICHAL, occurred_at=NOW)
    group.join(KASIA, occurred_at=NOW)
    group.pull_events()

    group.rename(GroupName("Ogrody nights"), occurred_at=LATER, **answered_by_marta())
    admitted = group.change_join_policy(
        JoinPolicy.ANYONE, occurred_at=LATER, **answered_by_marta()
    )

    renamed, changed, *approvals = group.pull_events()
    assert isinstance(renamed, GroupRenamed)
    assert renamed.renamed_by == MARTA_ACCOUNT
    assert isinstance(changed, JoinPolicyChanged)
    assert admitted == (MICHAL, KASIA)
    assert [approval.player_id for approval in approvals] == [MICHAL, KASIA]
    assert {approval.approved_by for approval in approvals} == {MARTA_ACCOUNT}


def test_a_player_group_has_no_whatsapp_size_or_declared_sports_to_set():
    group = Group.create_player_group(
        group_id=uuid4(),
        name=GroupName("Kazimierz crew"),
        home_club_id=CLUB,
        join_policy=JoinPolicy.ANYONE,
        owner_id=MICHAL,
        code=GroupCode("ab3de7fg"),
        occurred_at=NOW,
    )

    with pytest.raises(InvariantViolated):
        group.set_whatsapp_size(WhatsAppSize(52), by=MICHAL, occurred_at=LATER)
    with pytest.raises(InvariantViolated):
        group.declare_sports(
            DeclaredSports.of([Sport.PADEL]), by=MICHAL, occurred_at=LATER
        )


# --------------------------------------------------------------------------- #
# No way out for its administrator, and the ordinary way out for a member
# --------------------------------------------------------------------------- #


def test_nobody_deletes_an_official_group():
    group = ogrody_33_club()

    with pytest.raises(NotTheGroupOwner):
        group.delete(by=MARTA_ACCOUNT, occurred_at=LATER)


def test_its_administrator_who_joined_as_a_player_leaves_as_one_and_still_runs_it():
    group = ogrody_33_club()
    group.join(MICHAL, occurred_at=NOW)
    group.approve(MICHAL, occurred_at=NOW, **answered_by_marta())
    group.join(MARTA_ACCOUNT, occurred_at=NOW, runs_it=True)
    group.pull_events()

    group.leave(MARTA_ACCOUNT, occurred_at=LATER)

    (left,) = group.pull_events()
    assert isinstance(left, GroupLeft)
    assert group.administrator_id == MARTA
    assert list(group.members) == [MICHAL]


def test_the_last_member_leaves_an_official_group_and_it_stays():
    group = ogrody_33_club(JoinPolicy.ANYONE)
    group.join(MICHAL, occurred_at=NOW)
    group.pull_events()

    group.leave(MICHAL, occurred_at=LATER)

    (left,) = group.pull_events()
    assert isinstance(left, GroupLeft)
    assert group.members == {}
    assert not group.is_deleted


# --------------------------------------------------------------------------- #
# The handover
# --------------------------------------------------------------------------- #


def test_the_club_hands_it_over_and_only_who_answers_changes():
    group = ogrody_33_club()
    group.join(MICHAL, occurred_at=NOW)
    group.join(KASIA, occurred_at=NOW)
    group.approve(KASIA, occurred_at=NOW, **answered_by_marta())
    group.join(MARTA_ACCOUNT, occurred_at=NOW, runs_it=True)
    group.pull_events()

    group.assign_administrator(OLA, by=DESK, occurred_at=LATER)

    (assigned,) = group.pull_events()
    assert assigned == AdministratorAssigned(
        group_id=group.id, administrator_id=OLA, assigned_by=DESK, occurred_at=LATER
    )
    assert group.administrator_id == OLA
    # The request waits on the group, and nobody left it.
    assert list(group.waiting) == [MICHAL]
    assert list(group.members) == [KASIA, MARTA_ACCOUNT]
    assert group.code == GroupCode("ab3de7fg")
    assert group.join_policy is JoinPolicy.PEOPLE_I_APPROVE
    assert group.whatsapp_size == WhatsAppSize(48)


def test_after_a_handover_the_new_administrator_answers_and_the_old_one_cannot():
    group = ogrody_33_club()
    group.join(MICHAL, occurred_at=NOW)
    group.assign_administrator(OLA, by=DESK, occurred_at=LATER)
    group.pull_events()

    with pytest.raises(NotTheGroupOwner):
        group.approve(MICHAL, occurred_at=LATER, **answered_by_marta())
    group.approve(MICHAL, by=OLA_ACCOUNT, as_administrator=OLA, occurred_at=LATER)

    (approved,) = group.pull_events()
    assert approved == JoinRequestApproved(
        group_id=group.id, player_id=MICHAL, approved_by=OLA_ACCOUNT, occurred_at=LATER
    )


def test_handing_it_to_whoever_runs_it_already_records_nothing():
    group = ogrody_33_club()

    group.assign_administrator(MARTA, by=DESK, occurred_at=LATER)

    assert group.pull_events() == []


def test_the_handover_folds_back_out_of_the_stream():
    group = ogrody_33_club()
    created = Group.create_official_group(
        group_id=group.id,
        name=GroupName("Ogrody 33 Club"),
        club_id=CLUB,
        join_policy=JoinPolicy.PEOPLE_I_APPROVE,
        administrator_id=MARTA,
        created_by=MARTA_ACCOUNT,
        whatsapp_size=WhatsAppSize(48),
        sports=DeclaredSports.of([Sport.PADEL]),
        code=GroupCode("ab3de7fg"),
        occurred_at=NOW,
    ).pull_events()
    group.assign_administrator(OLA, by=DESK, occurred_at=LATER)

    replayed = Group.from_history([*created, *group.pull_events()])

    assert replayed.administrator_id == OLA
    assert replayed.version == 2


def test_a_player_group_is_never_handed_over():
    group = Group.create_player_group(
        group_id=uuid4(),
        name=GroupName("Kazimierz crew"),
        home_club_id=CLUB,
        join_policy=JoinPolicy.ANYONE,
        owner_id=MICHAL,
        code=GroupCode("ab3de7fg"),
        occurred_at=NOW,
    )

    with pytest.raises(InvariantViolated):
        group.assign_administrator(OLA, by=DESK, occurred_at=LATER)
