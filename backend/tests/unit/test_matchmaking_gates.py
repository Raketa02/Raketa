"""Stage 1 — the ten gates, and the two rules that decide all of them.

*A gate that cannot be evaluated excludes; a term that cannot be evaluated stands
down.* And *no relaxation reaches a gate.*

Most of what is asserted here is a **refusal**: that gender is applied in both
directions and reveals nothing, that a blank grid is not a gate, that the
histogram's key set is the whole closed roster, and that being excluded twice is
counted once and always under the same code.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

import pytest

from app.engines.matchfit.core import SearchMode
from app.modules.matchmaking.domain.gates import GATE_ROSTER, GateCode, gate_of
from app.modules.matchmaking.domain.search_context import NEWCOMER_WINDOW
from app.modules.matchmaking.domain.searches import SearchInitiation
from app.modules.matchmaking.domain.shortlist import generate
from app.modules.player_profile.domain.gender import Gender, GenderPreference
from tests.unit import matchmaking_builders as build


def _gate(candidate, **context_kwargs):
    context = build.context((candidate,), **context_kwargs)
    return gate_of(candidate, context, distance_km=0.0)


def test_the_roster_is_ten_and_the_histogram_is_keyed_on_all_of_them():
    """Ten codes, and a gate that excluded nobody is a recorded **zero**.

    A histogram that only carried the gates that fired would make *nobody was
    blocked* and *nobody was asked* the same shape, and the second is what a
    broken gate looks like.
    """

    assert len(GATE_ROSTER) == 10
    generated = generate(build.context((build.row(1),)))
    assert set(generated.excluded_by_gate) == {code.value for code in GateCode}
    assert sum(generated.excluded_by_gate.values()) == 0


def test_a_block_in_either_direction_excludes():
    """Live, never the index, and the set does not say which way it went."""

    candidate = build.row(1)
    assert _gate(candidate, blocked=frozenset({candidate.player_id})) is (
        GateCode.BLOCKED
    )


def test_a_held_account_excludes():
    candidate = build.row(1)
    assert _gate(candidate, held=frozenset({candidate.player_id})) is (
        GateCode.HELD_ACCOUNT
    )


def test_an_account_that_may_not_be_shown_excludes():
    candidate = build.row(1)
    assert _gate(candidate, unshowable=frozenset({candidate.player_id})) is (
        GateCode.ACCOUNT_INACTIVE
    )


def test_an_open_challenge_between_you_excludes():
    candidate = build.row(1)
    assert _gate(candidate, open_challenges=frozenset({candidate.player_id})) is (
        GateCode.OPEN_CHALLENGE
    )


def test_a_row_carrying_no_rating_for_this_sport_excludes():
    assert _gate(build.row(1, rating_status="")) is GateCode.NOT_RATED
    assert _gate(build.row(1, sport="TENNIS")) is GateCode.NOT_RATED


def test_the_radius_is_the_circle_and_not_the_box():
    """The bounding box admits its own corners; the gate is the ring inside it."""

    candidate = build.row(1)
    context = build.context((candidate,))

    assert gate_of(candidate, context, distance_km=9.9) is None
    assert gate_of(candidate, context, distance_km=10.1) is GateCode.OUTSIDE_RADIUS


def test_the_photo_gate_is_enumerated_and_excludes_nobody_today():
    """**Live and inert.** Neither half of *missing or unapproved* has a
    search-time provider: no verdict is stored against a player, and the index
    holds no photo fact by decision. It stays on the roster so the day it can
    bind, it binds — and so the roster stays ten rather than quietly nine."""

    assert GateCode.PHOTO in GATE_ROSTER
    assert _gate(build.row(1, proposals_opt_in=None)) is not GateCode.PHOTO


def test_the_proposals_opt_out_gates_the_push_and_not_the_person():
    """It reads ``initiation`` and never ``surface``: somebody who asked not to
    be pushed at is a full candidate in a search a human ran."""

    opted_out = build.row(1, proposals_opt_in=False)

    assert _gate(opted_out, initiation=SearchInitiation.HUMAN) is None
    assert _gate(opted_out, initiation=SearchInitiation.ENGINE) is (
        GateCode.PROPOSALS_OPT_OUT
    )


def test_an_unanswered_opt_in_is_not_an_opt_out():
    """*Explicitly false* is the rule. A profile committed before the question
    existed answered nothing, and nothing is not a refusal."""

    opted_nothing = build.row(1, proposals_opt_in=None)
    assert _gate(opted_nothing, initiation=SearchInitiation.ENGINE) is None


@pytest.mark.parametrize(
    "preference,gender,excluded",
    [
        (GenderPreference.ANY, "MAN", False),
        (GenderPreference.WOMEN_ONLY, "WOMAN", False),
        (GenderPreference.WOMEN_ONLY, "MAN", True),
        (GenderPreference.WOMEN_ONLY, None, True),
        (GenderPreference.WOMEN_ONLY, "PREFER_NOT_TO_SAY", True),
        (GenderPreference.MEN_ONLY, "MAN", False),
        (GenderPreference.MEN_ONLY, "WOMAN", True),
    ],
)
def test_the_searchers_preference_binds_the_candidate(preference, gender, excluded):
    """One direction of the mutual gate, and **absence excludes**.

    ``None`` is not a quieter ``PREFER_NOT_TO_SAY``: it is a profile committed
    before anybody was asked, and a preference that needs a gender and does not
    have one is a gate that could not be evaluated.
    """

    refused = _gate(
        build.row(1, gender=gender),
        facts=build.searcher(gender_preference=preference),
    )
    assert (refused is GateCode.GENDER_PREFERENCE) is excluded


@pytest.mark.parametrize(
    "their_preference,my_gender,excluded",
    [
        ("ANY", Gender.WOMAN, False),
        ("WOMEN_ONLY", Gender.WOMAN, False),
        ("WOMEN_ONLY", Gender.MAN, True),
        ("MEN_ONLY", Gender.WOMAN, True),
        ("WOMEN_ONLY", None, True),
    ],
)
def test_the_candidates_preference_binds_the_searcher(
    their_preference, my_gender, excluded
):
    """**The other direction**, which is what makes the gate mutual: it protects
    the candidate's inbox as well as the searcher's list."""

    refused = _gate(
        build.row(1, gender_preference=their_preference),
        facts=build.searcher(gender=my_gender),
    )
    assert (refused is GateCode.GENDER_PREFERENCE) is excluded


def test_a_preference_this_build_cannot_read_excludes():
    """A safety setting we cannot evaluate has one safe reading, and it is the
    strictest. The asymmetry with an unreadable *answer* — which is an absence —
    is the same rule from the other side."""

    assert _gate(build.row(1, gender_preference="FROM_A_LATER_VOCABULARY")) is (
        GateCode.GENDER_PREFERENCE
    )


def test_the_level_gate_reads_the_tolerance_the_curve_uses():
    """``Δμ < LEVEL_TOL_mode``, and the two numbers are the same number — so the
    gate and the curve cannot drift apart."""

    settled = build.searcher(profile_created_at=build.SETTLED)
    just_inside = build.row(1, mu=build.SEARCHER_MU + 0.54)
    just_outside = build.row(2, mu=build.SEARCHER_MU + 0.56)

    assert _gate(just_inside, facts=settled) is None
    assert _gate(just_outside, facts=settled) is GateCode.LEVEL


def test_for_fun_reads_its_own_wider_tolerance():
    wider = build.row(1, mu=build.SEARCHER_MU + 0.80)
    assert _gate(wider, facts=build.searcher(mode=SearchMode.COMPETITIVE)) is (
        GateCode.LEVEL
    )
    assert _gate(wider, facts=build.searcher(mode=SearchMode.FOR_FUN)) is None


def test_newness_tightens_the_gate_on_both_sides_of_the_pairing():
    """**Newness changes the gate, never the weights.**

    It binds the *pairing* and not the search: gating only the newcomer's own
    search would leave the bad first game arriving through the veteran's list.
    """

    wider = build.row(1, mu=build.SEARCHER_MU + 0.80)
    a_new_candidate = build.row(
        2,
        mu=build.SEARCHER_MU + 0.80,
        profile_created_at=build.NOW - NEWCOMER_WINDOW + timedelta(days=1),
    )
    a_new_searcher = build.searcher(
        mode=SearchMode.FOR_FUN,
        profile_created_at=build.NOW - NEWCOMER_WINDOW + timedelta(days=1),
    )
    for_fun = build.searcher(mode=SearchMode.FOR_FUN)

    assert _gate(wider, facts=for_fun) is None, "the veteran pairing is inside for fun"
    assert _gate(a_new_candidate, facts=for_fun) is GateCode.LEVEL
    assert _gate(wider, facts=a_new_searcher) is GateCode.LEVEL


def test_a_blank_availability_grid_is_not_a_gate_and_never_was():
    """It means *we do not know*, and the availability term stands down. A
    player who cleared their week did not say they are never free."""

    assert _gate(build.row(1, slots=())) is None


def test_two_gates_on_one_candidate_are_counted_once_under_the_first():
    """A histogram whose keys depended on evaluation order is a histogram nobody
    can compare across releases, so the order is the roster's own."""

    candidate = build.row(1, gender=None)
    generated = generate(
        build.context(
            (candidate,),
            blocked=frozenset({candidate.player_id}),
            facts=build.searcher(gender_preference=GenderPreference.WOMEN_ONLY),
        )
    )

    assert generated.excluded_by_gate[GateCode.BLOCKED.value] == 1
    assert generated.excluded_by_gate[GateCode.GENDER_PREFERENCE.value] == 0
    assert sum(generated.excluded_by_gate.values()) == 1


def test_the_searcher_is_dropped_before_the_gates_and_never_counted():
    """Being yourself is not an exclusion anybody is owed a count of, and a gate
    for it would put a permanent 1 in every histogram."""

    somebody_else = generate(build.context((build.row(1),)))
    assert somebody_else.n_generated == 1

    myself = replace(build.row(1), player_id=str(build.SEARCHER_ID))
    mine = generate(build.context((myself,)))

    assert mine.n_generated == 0
    assert sum(mine.excluded_by_gate.values()) == 0


def test_no_relaxation_reaches_a_gate():
    """Asserted on the **signature**, because that is where it is enforced: there
    is no rung argument to pass and none to add."""

    from inspect import signature

    assert set(signature(gate_of).parameters) == {"row", "context", "distance_km"}
