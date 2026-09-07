"""Stage 4 — the modifiers, the budget that holds them, and the dock outside it.

The two claims worth a test here are the ones a reading of the code cannot
settle. **The budget binds the stack and not the modifier**, which is only
observable when more than one fires — so the property test below drives every
combination of the three at both ends of their ranges rather than the day-one
case where one of them can fire at all. And **the reliability dock is outside
it**, which is only observable when the stack is already at its positive ceiling.

The struck pair is asserted by absence, over the roster rather than over this
module: a test that language does not fire would pass just as well against a
version that had it and never called it.
"""

from __future__ import annotations

from inspect import signature
from itertools import product

import pytest

from app.engines.matchfit.core import (
    FamiliarityReading,
    Modifier,
    ReliabilityStrand,
    SearchMode,
)
from app.engines.matchfit.ranking import ModifiedFit, ModifierPoints, ModifierStack
from app.engines.matchfit.ruleset import BUDGETED_MODIFIERS
from app.engines.matchfit.scorable import SharedHistory
from app.engines.matchfit.v1 import (
    absorbed,
    calibration_value,
    familiarity,
    modify,
    reading_for,
    reliability_floor_breach,
    score,
    strength_of,
    welcoming_record,
)
from app.kernel import InvariantViolated
from app.modules.matchmaking.infrastructure.rulesets import LIVE_RULESET
from app.modules.player_profile.domain.social_tags import SocialTag
from tests.unit.matchfit_builders import (
    candidate,
    capped_at,
    modifier_facts,
    record,
    searcher,
)

#: One strand, because a record refuses to exist without one — and the reliability
#: **floor** does not read the strands at all, which is what these tests are about.
ONE_STRAND = {ReliabilityStrand.SHOWS_UP: (95, 40)}

RULES = LIVE_RULESET.modifiers


def stack(
    *fired: ModifierPoints, breach: ModifierPoints | None = None
) -> ModifierStack:
    return ModifierStack(fired=fired, floor_breach=breach, rules=RULES)


def points(modifier: Modifier, value: float) -> ModifierPoints:
    return ModifierPoints(modifier=modifier, points=value)


# ---------------------------------------------------------------------------
# The roster: three, and the two that are struck
# ---------------------------------------------------------------------------


def test_the_roster_is_three_budgeted_modifiers_and_one_dock_outside() -> None:
    """Four names, and the two struck ones are absent from the vocabulary itself.

    Asserted over ``Modifier`` rather than over this module's behaviour: a test
    that *language never fires* passes against a version that has the modifier
    and forgot to call it, which is the shape of the bug that would bring it
    back.
    """

    assert set(BUDGETED_MODIFIERS) | {Modifier.RELIABILITY_FLOOR_BREACH} == set(
        Modifier
    )
    assert len(Modifier) == 4
    assert Modifier.RELIABILITY_FLOOR_BREACH not in RULES.ranges


@pytest.mark.parametrize("struck", ["LANGUAGE", "SHARED_LANGUAGE", "INTENT_OPPOSED"])
def test_language_and_intent_opposition_are_not_in_the_vocabulary(struck: str) -> None:
    """*A protected characteristic may gate; it may never score* — and the second
    charge for an opposite declaration is a gate wearing a modifier's clothes."""

    assert struck not in {modifier.name for modifier in Modifier}


# ---------------------------------------------------------------------------
# Calibration value — the only modifier whose input exists
# ---------------------------------------------------------------------------


def test_calibration_is_binary_and_reads_the_ranges_own_maximum() -> None:
    """Two values in, two values out. ``calibration_priority`` has no middle."""

    fired = calibration_value(
        searcher(), modifier_facts(calibration_elevated=True), LIVE_RULESET
    )
    assert fired == points(
        Modifier.CALIBRATION_VALUE,
        float(RULES.ranges[Modifier.CALIBRATION_VALUE].maximum),
    )


def test_calibration_does_not_fire_in_a_friendly() -> None:
    """It applies where a rating is at stake, and a for-fun game is never counted."""

    assert (
        calibration_value(
            searcher(mode=SearchMode.FOR_FUN),
            modifier_facts(calibration_elevated=True),
            LIVE_RULESET,
        )
        is None
    )


def test_a_standard_calibration_is_absent_rather_than_zero() -> None:
    """A modifier worth nothing prints nothing, so it is not in the stack."""

    assert calibration_value(searcher(), modifier_facts(), LIVE_RULESET) is None


# ---------------------------------------------------------------------------
# Familiarity — signed by the searcher's own tags
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("tags", "reading"),
    [
        ((SocialTag.HERE_FOR_A_REGULAR_GAME.value,), FamiliarityReading.REPETITION),
        ((SocialTag.HERE_TO_MEET_PLAYERS.value,), FamiliarityReading.VARIETY),
        ((SocialTag.HERE_TO_COMPETE.value,), FamiliarityReading.NEITHER),
        ((), FamiliarityReading.NEITHER),
    ],
)
def test_the_reading_comes_off_the_searchers_declared_tags(
    tags: tuple[str, ...], reading: FamiliarityReading
) -> None:
    assert reading_for(tags, LIVE_RULESET.tags) is reading


def test_repetition_wins_a_tie() -> None:
    """*I want a regular game* and *I want to meet people* is read as the first.

    The claim that is specific about **who** wins, which is #164's rule: the
    alternative is a player who told the product exactly what they wanted being
    matched away from it by a second tag that says nothing about repetition.
    """

    both = (
        SocialTag.HERE_TO_MEET_PLAYERS.value,
        SocialTag.HERE_FOR_A_REGULAR_GAME.value,
    )
    assert reading_for(both, LIVE_RULESET.tags) is FamiliarityReading.REPETITION


def test_familiarity_is_read_from_the_searcher_and_never_the_candidate() -> None:
    """The one asymmetry in Fit, and the reason a matrix row needs no direction.

    Asserted over the **signature** rather than over a pair of readings: a test
    that varied the candidate's tags and saw no change would pass equally against
    a version that read them and happened to weigh them at nothing. The candidate
    is not an argument, so there is nothing to read.
    """

    assert "candidate" not in signature(familiarity).parameters
    history = SharedHistory(days_since_last_game=0, games_played_together=1)
    repeats = searcher(tags=(SocialTag.HERE_FOR_A_REGULAR_GAME.value,))
    fired = familiarity(repeats, modifier_facts(shared_history=history), LIVE_RULESET)
    assert fired is not None and fired.points > 0


def test_an_eight_month_old_single_game_is_effectively_fresh_again() -> None:
    """§9.4's own claim, as the number the half-life and φ actually produce."""

    strength = strength_of(
        SharedHistory(days_since_last_game=240, games_played_together=1), LIVE_RULESET
    )
    assert strength == pytest.approx(0.5 ** (240 / 90) * (1 - 0.45), abs=1e-9)
    assert strength == pytest.approx(0.087, abs=0.001)


def test_a_variety_seeker_is_docked_where_a_repetition_seeker_is_paid() -> None:
    """The signed arm, and the asymmetry between the two ends.

    Being wrong about a positive costs a duller evening; being wrong about a
    negative buries a person — so the negative arm is the smaller one, and that
    is a fact about the range rather than about this call.
    """

    history = SharedHistory(days_since_last_game=0, games_played_together=100)
    facts = modifier_facts(shared_history=history)
    repeats = familiarity(
        searcher(tags=(SocialTag.HERE_FOR_A_REGULAR_GAME.value,)), facts, LIVE_RULESET
    )
    varies = familiarity(
        searcher(tags=(SocialTag.HERE_TO_MEET_PLAYERS.value,)), facts, LIVE_RULESET
    )
    assert repeats is not None and varies is not None
    assert repeats.points > 0 > varies.points
    assert abs(varies.points) < repeats.points


def test_a_reader_who_said_neither_leans_mildly_towards_novelty() -> None:
    """At most half the negative arm — §9.4's *mildly novelty-preferring*."""

    history = SharedHistory(days_since_last_game=0, games_played_together=100)
    fired = familiarity(
        searcher(tags=(SocialTag.HERE_TO_COMPETE.value,)),
        modifier_facts(shared_history=history),
        LIVE_RULESET,
    )
    arm = RULES.ranges[Modifier.FAMILIARITY].minimum
    assert fired is not None
    assert fired.points == pytest.approx(arm * RULES.familiarity.default_lean, abs=0.01)


def test_no_shared_history_is_an_absence_and_not_a_novelty_bonus() -> None:
    """Two people who have never played are not *maximally novel*: the modifier
    reads a history, and there is none to read."""

    assert familiarity(searcher(), modifier_facts(), LIVE_RULESET) is None


def test_a_shared_history_of_no_games_refuses_to_exist() -> None:
    with pytest.raises(InvariantViolated):
        SharedHistory(days_since_last_game=10, games_played_together=0)


# ---------------------------------------------------------------------------
# The welcoming record — one unpaid input
# ---------------------------------------------------------------------------


def test_the_welcoming_record_reads_one_input_and_no_answer_is_not_a_no() -> None:
    """Both ``None`` and ``False`` leave the stack empty, and they are different
    facts: the provider is ``matches``, which does not exist."""

    no_answer = modifier_facts()
    assert no_answer.welcomed_settling_opponents is None
    assert welcoming_record(no_answer, LIVE_RULESET) is None
    measured_no = modifier_facts(welcomed_settling_opponents=False)
    assert measured_no.welcomed_settling_opponents is False
    assert welcoming_record(measured_no, LIVE_RULESET) is None
    fired = welcoming_record(
        modifier_facts(welcomed_settling_opponents=True), LIVE_RULESET
    )
    assert fired == points(
        Modifier.WELCOMING_RECORD,
        float(RULES.ranges[Modifier.WELCOMING_RECORD].maximum),
    )


# ---------------------------------------------------------------------------
# The absorption cap — wired, and never binding
# ---------------------------------------------------------------------------

CAPPED_AT_TWO = capped_at(2)


def test_the_shipped_ruleset_never_binds_the_cap() -> None:
    """**Wired, never binding.** The tally is counted, carried and read, and no
    comparison against a ``None`` cap can be true — so a player volunteered a
    thousand times this week keeps every point the record earns them."""

    assert LIVE_RULESET.modifiers.newcomer_absorption_cap is None
    assert not absorbed(1000, LIVE_RULESET.modifiers)
    assert (
        welcoming_record(
            modifier_facts(
                welcomed_settling_opponents=True, newcomer_appearances=1000
            ),
            LIVE_RULESET,
        )
        is not None
    )


def test_a_search_that_is_not_a_newcomers_has_nothing_to_bound() -> None:
    """``None`` appearances is *this search is not a newcomer's*, and it is a
    different fact from a counted zero — the bound is on the ask, so a search
    adding nothing to somebody's absorption may not take anything away for it."""

    assert not absorbed(None, CAPPED_AT_TWO.modifiers)
    assert absorbed(0, CAPPED_AT_TWO.modifiers) is False


def test_the_cap_binds_at_it_and_not_past_it() -> None:
    """*How often* — the appearance that reaches the cap is the last one the
    engine volunteers them for."""

    rules = CAPPED_AT_TWO.modifiers
    assert not absorbed(1, rules)
    assert absorbed(2, rules)
    assert absorbed(3, rules)


def test_past_the_cap_the_welcoming_modifier_is_dropped_and_nothing_else() -> None:
    """The record is still true; the engine has stopped paying for it.

    ``docs/adr/0114``: *it removes the engine's thumb, not the player* — so the
    stack loses the welcoming line and keeps whatever else fired, and no shape
    here can withhold anybody.
    """

    welcomed = modifier_facts(
        welcomed_settling_opponents=True, calibration_elevated=True
    )
    absorbed_too_often = modifier_facts(
        welcomed_settling_opponents=True,
        calibration_elevated=True,
        newcomer_appearances=2,
    )

    freely = modify(searcher(), candidate(), welcomed, CAPPED_AT_TWO)
    capped = modify(searcher(), candidate(), absorbed_too_often, CAPPED_AT_TWO)

    assert {entry.modifier for entry in freely.fired} == {
        Modifier.WELCOMING_RECORD,
        Modifier.CALIBRATION_VALUE,
    }
    assert {entry.modifier for entry in capped.fired} == {
        Modifier.CALIBRATION_VALUE
    }


# ---------------------------------------------------------------------------
# The reliability floor — outside the budget, on the published score
# ---------------------------------------------------------------------------


def test_the_dock_reads_the_published_player_score_and_not_the_blend() -> None:
    """The one deliberate place the matcher reads the blend, recorded as such.

    A candidate whose strands are excellent and whose *published* figure is under
    the bar still takes the dock — which is the whole point: the penalty has to
    be justified by a figure a human can look at.
    """

    under = candidate(reliability=record(published_score=69, ratios=ONE_STRAND))
    fired = reliability_floor_breach(under, LIVE_RULESET)
    assert fired == points(
        Modifier.RELIABILITY_FLOOR_BREACH, float(RULES.floor_breach_penalty)
    )


def test_the_bar_is_a_dock_at_the_bar_and_not_below_it() -> None:
    at_the_bar = candidate(
        reliability=record(
            published_score=LIVE_RULESET.reliability.published_score_bar,
            ratios=ONE_STRAND,
        )
    )
    assert reliability_floor_breach(at_the_bar, LIVE_RULESET) is None


def test_a_candidate_with_no_record_takes_no_dock() -> None:
    """An absent Player Score is not a low one, so there is nothing to breach."""

    assert reliability_floor_breach(candidate(), LIVE_RULESET) is None


def test_the_dock_is_derived_from_the_budget_and_sits_outside_it() -> None:
    """``budget + 1`` — the smallest penalty a full positive stack cannot erase."""

    assert RULES.floor_breach_penalty == -(RULES.budget + 1)
    full = stack(
        *(
            points(modifier, RULES.ranges[modifier].maximum)
            for modifier in BUDGETED_MODIFIERS
        ),
        breach=points(
            Modifier.RELIABILITY_FLOOR_BREACH, float(RULES.floor_breach_penalty)
        ),
    )
    assert full.budgeted == RULES.budget
    assert full.applied < 0


# ---------------------------------------------------------------------------
# The budget — on the stack, and the property that says so
# ---------------------------------------------------------------------------


#: **Every** combination the three ranges admit, not their corners. §17.3 asks for
#: the whole space and it is 250 rows — a clamp is linear and its corners would do,
#: which is exactly the reasoning that stops being true the first time a modifier
#: gains a curve.
EVERY_STACK = list(
    product(
        *(
            range(RULES.ranges[modifier].minimum, RULES.ranges[modifier].maximum + 1)
            for modifier in BUDGETED_MODIFIERS
        )
    )
)


@pytest.mark.parametrize(
    "combination",
    EVERY_STACK,
    ids=lambda combination: ",".join(str(value) for value in combination),
)
def test_the_budgeted_stack_never_leaves_the_budget(
    combination: tuple[int, ...],
) -> None:
    """Every modifier at every value in its own range, and the stack still holds.

    The property is over the **whole** space and not over the subsets today's
    inputs reach: two of the three cannot fire at all until ``matches`` lands, and
    a budget only ever exercised by the one that can is a budget that breaks on
    the day it starts doing work.
    """

    built = stack(
        *(
            points(modifier, float(value))
            for modifier, value in zip(BUDGETED_MODIFIERS, combination, strict=True)
        )
    )
    assert -RULES.budget <= built.budgeted <= RULES.budget
    assert built.applied == built.budgeted


def test_the_budget_is_reachable_from_both_ends() -> None:
    """The check that stops the property above passing vacuously.

    A budget nothing in the space can reach is a budget that holds because it is
    unreachable, which is indistinguishable from one that holds because it works.
    """

    reached = {
        stack(
            *(
                points(modifier, float(value))
                for modifier, value in zip(BUDGETED_MODIFIERS, combination, strict=True)
            )
        ).budgeted
        for combination in EVERY_STACK
    }
    assert max(reached) == RULES.budget
    assert min(reached) < 0


def test_a_stack_of_small_positives_cannot_lift_somebody_over_a_no_show() -> None:
    """The budget's entire argument, as the inequality it exists to keep."""

    everything = stack(
        *(
            points(modifier, RULES.ranges[modifier].maximum)
            for modifier in BUDGETED_MODIFIERS
        ),
        breach=points(
            Modifier.RELIABILITY_FLOOR_BREACH, float(RULES.floor_breach_penalty)
        ),
    )
    assert everything.applied == RULES.budget + RULES.floor_breach_penalty
    assert everything.applied == -1


def test_the_clamp_records_whether_it_bound() -> None:
    """Its own falsifier: never binding and binding often are opposite failures."""

    inside = stack(points(Modifier.CALIBRATION_VALUE, 4.0))
    assert not inside.clamped
    over = stack(
        points(Modifier.CALIBRATION_VALUE, 8.0), points(Modifier.FAMILIARITY, 5.0)
    )
    assert over.clamped and over.budgeted == RULES.budget


def test_a_modifier_firing_twice_refuses_to_exist() -> None:
    with pytest.raises(InvariantViolated):
        stack(
            points(Modifier.CALIBRATION_VALUE, 4.0),
            points(Modifier.CALIBRATION_VALUE, 4.0),
        )


def test_only_the_reliability_breach_may_sit_outside_the_budget() -> None:
    """A second dock outside the budget would be a budget with a hole in it."""

    with pytest.raises(InvariantViolated):
        stack(breach=points(Modifier.CALIBRATION_VALUE, 4.0))


# ---------------------------------------------------------------------------
# `modify` — the roster, in order, once
# ---------------------------------------------------------------------------


def test_the_stack_is_read_in_the_rosters_own_order() -> None:
    fired = modify(
        searcher(tags=(SocialTag.HERE_FOR_A_REGULAR_GAME.value,)),
        candidate(),
        modifier_facts(
            calibration_elevated=True,
            shared_history=SharedHistory(
                days_since_last_game=0, games_played_together=2
            ),
            welcomed_settling_opponents=True,
        ),
        LIVE_RULESET,
    )
    assert tuple(entry.modifier for entry in fired.fired) == BUDGETED_MODIFIERS


def test_on_day_one_nothing_fires_at_all_unless_calibration_does() -> None:
    """The state of the platform, asserted rather than described.

    ``matches`` is unwritten, so two of the three have no answer and the third is
    the whole of the stack — which is why the budget is inert today and why the
    property test above drives the space it cannot yet reach.
    """

    empty = modify(searcher(), candidate(), modifier_facts(), LIVE_RULESET)
    assert empty.fired == () and empty.floor_breach is None and empty.applied == 0.0


def test_a_modified_fit_keeps_its_terms_adding_up_to_the_unmodified_number() -> None:
    """*Why 78?* reconciles to the Fit; the modifiers are a printed list beside it."""

    fit = score(searcher(), candidate(), LIVE_RULESET)
    modified = ModifiedFit(
        fit=fit, modifiers=stack(points(Modifier.CALIBRATION_VALUE, 4.0))
    )
    assert sum(term.contribution for term in fit.terms) == pytest.approx(fit.points)
    assert modified.points == pytest.approx(fit.points + 4.0)


def test_the_scale_bounds_the_stack_and_never_the_total() -> None:
    """A score out of a hundred stays on its scale, **and still adds up**.

    Clamping the total would leave the printed number smaller than its own
    parts — the one thing this stage may not do — so what the scale bounds is
    what the stack may spend. The disagreement is between ``modifiers.applied``
    and what was actually applied, and it has a name.
    """

    fit = score(searcher(), candidate(), LIVE_RULESET)
    ceiling = ModifiedFit(
        fit=fit, modifiers=stack(points(Modifier.CALIBRATION_VALUE, 400.0))
    )
    assert ceiling.points == 100.0
    assert ceiling.points == pytest.approx(fit.points + ceiling.applied)
    basement = ModifiedFit(
        fit=fit,
        modifiers=stack(breach=points(Modifier.RELIABILITY_FLOOR_BREACH, -400.0)),
    )
    assert basement.points == 0.0
    assert basement.points == pytest.approx(fit.points + basement.applied)


def test_the_printed_number_is_always_the_fit_plus_what_was_applied() -> None:
    """Over the whole stack space, and it is the reconcilability *Why 78?* needs."""

    fit = score(searcher(), candidate(), LIVE_RULESET)
    for combination in EVERY_STACK:
        modified = ModifiedFit(
            fit=fit,
            modifiers=stack(
                *(
                    points(modifier, float(value))
                    for modifier, value in zip(
                        BUDGETED_MODIFIERS, combination, strict=True
                    )
                )
            ),
        )
        assert modified.points == pytest.approx(fit.points + modified.applied)
        assert 0.0 <= modified.points <= 100.0
