"""A club's policy: exactly eight fields, and no platform floor under any of them.

Three claims, and each fails differently.

1. **The row is eight fields.** Asserted against the dataclass itself rather than
   against a list somebody keeps in step, so a ninth field with no named reader
   fails here — which is where ADR-0078 asks the next session to be stopped.
2. **`maxHoldAge` is three-valued and nothing floors it.** ``None``, a positive
   number honoured with no minimum, and ``0`` meaning *this club does not hold
   speculatively at all*. The projection onto the kernel's ``HoldPolicy`` is an
   identity on all four fields, which is the whole content of *no floor is
   applied anywhere*: there is no arithmetic for one to hide in.
3. **Two fields ship read by nobody**, and that is checked by a walk rather than
   claimed in a comment — see ``test_the_two_dark_fields_have_no_reader``.
"""

from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields
from pathlib import Path

import pytest

from app.kernel import HoldPolicy, hours, minutes
from app.modules.clubs.domain.policy import POLICY_FIELDS, ClubPolicy

ROOT = Path(__file__).resolve().parents[2]

#: The two fields ADR-0078 ships dark. `#64` is the ticket that shipped them.
DARK_FIELDS = ("free_cancel_hours", "counts_cash")

#: Where a dark field may legitimately be named: the context that stores it, and
#: the seed catalog that authors clubs. Anywhere else is a reader, which is the
#: thing ADR-0078 says does not exist yet.
DARK_FIELD_HOMES = ("app/modules/clubs/", "app/seeds/")


def test_the_policy_is_exactly_eight_fields():
    names = tuple(field.name for field in fields(ClubPolicy))

    assert names == POLICY_FIELDS
    assert len(names) == 8


def test_the_defaults_are_the_ones_the_adr_fixes():
    policy = ClubPolicy()

    assert policy.window == hours(24)
    assert policy.join_cut == minutes(30)
    assert policy.max_hold_age is None
    assert policy.prob_hold is False
    assert policy.rebooking_credit is False
    # `null`, not the prototype's 24: that 24 lived inside a refund table whose
    # money meaning ADR-0047 removed, and inheriting a number from a structure we
    # deleted is how a dead decision comes back.
    assert policy.free_cancel_hours is None
    assert policy.turnaround_min == minutes(0)
    # On, because every Polish racket club takes cash and entering nine of them
    # as *refuses cash* describes none of them.
    assert policy.counts_cash is True


def test_the_projection_onto_the_hold_ladder_is_an_identity():
    policy = ClubPolicy(
        window=hours(6),
        join_cut=minutes(5),
        max_hold_age=hours(1),
        prob_hold=True,
        rebooking_credit=True,
        free_cancel_hours=12,
        turnaround_min=minutes(15),
        counts_cash=False,
    )

    assert policy.hold_policy() == HoldPolicy(
        window=hours(6),
        join_cut=minutes(5),
        max_hold_age=hours(1),
        prob_hold=True,
    )


@pytest.mark.parametrize(
    "cap", [0, 1, 5, 30, 59, 60, 61, 359, 360, 1440, 10080, 525_600]
)
def test_no_platform_floor_is_applied_to_max_hold_age(cap):
    """*"`maxHoldAge: 1` is a hostile number wearing the costume of a setting"* —
    and it is honoured anyway. ADR-0078 refuses a floor as unenforceable against
    a club that simply stops publishing courts."""

    policy = ClubPolicy(max_hold_age=minutes(cap))

    assert policy.max_hold_age == cap
    assert policy.hold_policy().max_hold_age == cap


def test_zero_means_the_club_does_not_hold_speculatively_at_all():
    """A third value, not the smallest of the second kind. *"Said plainly rather
    than performed by a hold that dies an hour after it is granted."*"""

    assert ClubPolicy(max_hold_age=minutes(0)).holds_speculatively is False
    assert ClubPolicy(max_hold_age=minutes(1)).holds_speculatively is True
    assert ClubPolicy(max_hold_age=None).holds_speculatively is True


def test_none_and_zero_are_different_facts():
    never_stale = ClubPolicy(max_hold_age=None)
    never_holds = ClubPolicy(max_hold_age=minutes(0))

    assert never_stale != never_holds
    assert never_stale.hold_policy() != never_holds.hold_policy()


@pytest.mark.parametrize(
    "kwargs",
    [
        {"window": minutes(0)},
        {"window": minutes(-1)},
        {"join_cut": minutes(-1)},
        {"max_hold_age": minutes(-1)},
        {"free_cancel_hours": -1},
        {"turnaround_min": minutes(-1)},
    ],
)
def test_a_negative_or_zero_duration_is_refused(kwargs):
    with pytest.raises(ValueError):
        ClubPolicy(**kwargs)


def test_a_policy_is_frozen_so_a_change_cannot_be_an_update_in_place():
    """The whole shape depends on this: a policy is *replaced*, and the row that
    held the old one survives."""

    policy = ClubPolicy()

    with pytest.raises(FrozenInstanceError):
        policy.max_hold_age = minutes(0)  # type: ignore[misc]


def _names_read_in(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            found.add(node.attr)
        elif isinstance(node, ast.Name):
            found.add(node.id)
        elif isinstance(node, ast.keyword) and node.arg:
            found.add(node.arg)
    return found


def test_the_two_dark_fields_have_no_reader():
    """*"Do not read that silence as nobody needed this"* — stated where it fails.

    `freeCancelHours`' only two consumers are the owner messages ruled out of
    scope on #44; `countsCash` is gated off by the missing marking surface, and
    ADR-0059's refusal rule for a late mark is therefore unexercised in v1. The
    walk allows the Clubs context (which stores them) and the seed catalog (which
    authors clubs); anywhere else in `app/` naming one is a reader.

    When one appears, this test is what has to be edited — and editing it is the
    moment somebody reads ADR-0078 and ADR-0059's precondition.
    """

    offenders = {
        str(path.relative_to(ROOT)): sorted(
            name for name in _names_read_in(path) if name in DARK_FIELDS
        )
        for path in sorted((ROOT / "app").rglob("*.py"))
        if not str(path.relative_to(ROOT)).startswith(DARK_FIELD_HOMES)
    }
    assert {k: v for k, v in offenders.items() if v} == {}
    assert len(offenders) >= 100, "the walk has lost the tree it is claiming about"


def test_the_dark_fields_are_stored_and_read_back():
    """Dark is not absent. They cross the aggregate boundary intact, so the day a
    reader exists the value is there rather than defaulted."""

    policy = ClubPolicy(free_cancel_hours=24, counts_cash=False)

    assert policy.free_cancel_hours == 24
    assert policy.counts_cash is False
