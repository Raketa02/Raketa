"""Stage 5 — the quality floor, and the minimum evidence beside it.

**The floor's own bound is asserted in ``test_matchfit_judged_pairings.py``**,
against the six judged cases the integer is read off, and re-derived at release
time by ``make judged-pairings``. What is left for this file is the half those
cases cannot say: that the bar is **one** bar, that it reads the *modified*
number, and that the gate beside it counts a person's own gaps and never a
platform-wide absence.

The gate's day-one claim — **it excludes nobody** — is the one worth driving
hardest, because it is a claim that will stop being true silently. It is asserted
two ways: over the arithmetic the live set produces, and over the six judged
pairings, which are the only pinned pairings this repository has.
"""

from __future__ import annotations

from dataclasses import replace
from inspect import signature
from types import MappingProxyType

import pytest

from app.engines.matchfit.core import Modifier, SearchMode, Term
from app.engines.matchfit.ranking import ModifiedFit, ModifierPoints, ModifierStack
from app.engines.matchfit.ruleset import Ruleset
from app.engines.matchfit.scoring import Fit
from app.engines.matchfit.v1 import Refusal, admits, live_terms, score
from app.kernel import InvariantViolated
from app.modules.matchmaking.infrastructure.rulesets import LIVE_RULESET
from tests.unit.matchfit_builders import candidate, searcher

#: Reliability is the one term weighted here whose provider does not exist, so it
#: is the whole of *absent platform-wide* on day one. It is named rather than
#: derived, because *no provider exists* is a fact about the composition root and
#: a ruleset that could declare it would be a weight release deciding which
#: contexts are built.
DAY_ONE_ABSENT = frozenset({Term.RELIABILITY})

FLOORS = LIVE_RULESET.floors


def modified(fit: Fit, applied: float = 0.0) -> ModifiedFit:
    """A Fit with a stack that moves it by ``applied``, however it got there."""

    return ModifiedFit(
        fit=fit,
        modifiers=ModifierStack(
            fired=(),
            floor_breach=(
                None
                if applied == 0.0
                else ModifierPoints(
                    modifier=Modifier.RELIABILITY_FLOOR_BREACH, points=applied
                )
            ),
            rules=LIVE_RULESET.modifiers,
        ),
    )


def scored_but_for(*standing_down: Term) -> Fit:
    """A Fit carrying every live term except the named ones.

    Built by hand rather than by starving a candidate of inputs, because the
    gate is about **how many terms fired** and constructing each shortfall
    through a real pairing would test the terms again instead of the gate.
    """

    full = score(searcher(), candidate(), LIVE_RULESET)
    kept = tuple(term for term in full.terms if term.term not in standing_down)
    return Fit(
        points=sum(term.contribution for term in kept),
        terms=kept,
        degraded_terms=full.degraded_terms + tuple(standing_down),
        concerns=(),
        engine_version=full.engine_version,
        ruleset_version=full.ruleset_version,
    )


# ---------------------------------------------------------------------------
# One floor
# ---------------------------------------------------------------------------


def test_the_floor_takes_no_mode_no_sport_and_no_rung() -> None:
    """*One floor, both modes, every sport, never relaxed at any rung.*

    Said in the signature rather than in a docstring: there is no expression in
    this module for a bar that moved for whichever pool is thin, so lowering it
    quietly would take a new parameter and an argument for it.
    """

    taken = set(signature(admits).parameters)
    assert taken == {
        "modified",
        "ruleset",
        "absent",
        "newcomer",
        "interest_received",
    }
    assert not taken & {"mode", "sport", "rung", "searcher"}
    assert isinstance(FLOORS.quality_floor, int)


@pytest.mark.parametrize("mode", list(SearchMode))
def test_both_modes_are_judged_against_the_same_integer(mode: SearchMode) -> None:
    """The ruleset holds one ``quality_floor`` and it is not keyed by anything."""

    at_the_bar = score(searcher(mode=mode), candidate(), LIVE_RULESET)
    assert admits(modified(at_the_bar), LIVE_RULESET, DAY_ONE_ABSENT).admitted
    docked = modified(at_the_bar, applied=FLOORS.quality_floor - at_the_bar.points - 1)
    assert (
        admits(docked, LIVE_RULESET, DAY_ONE_ABSENT).refusal
        is Refusal.BELOW_QUALITY_FLOOR
    )


def test_the_bar_reads_the_modified_number_and_not_the_bare_fit() -> None:
    """Otherwise the reliability dock is decorative.

    A candidate whose Fit clears the bar and whose published Player Score is under
    it takes the dock, and the dock is what the bar sees — which is the whole
    reason stage 4 runs before stage 5.
    """

    fit = score(searcher(), candidate(), LIVE_RULESET)
    assert fit.points > FLOORS.quality_floor
    docked = modified(fit, applied=FLOORS.quality_floor - fit.points - 0.5)
    assert not admits(docked, LIVE_RULESET, DAY_ONE_ABSENT).admitted


def test_the_bar_is_inclusive_at_the_bar() -> None:
    """``min(Fit | shown)`` is the floor's upper bound, so the floor itself shows."""

    fit = score(searcher(), candidate(), LIVE_RULESET)
    exactly = modified(fit, applied=FLOORS.quality_floor - fit.points)
    assert exactly.points == pytest.approx(FLOORS.quality_floor)
    assert admits(exactly, LIVE_RULESET, DAY_ONE_ABSENT).admitted


# ---------------------------------------------------------------------------
# Minimum evidence — a gate, never a score adjustment
# ---------------------------------------------------------------------------


def test_the_live_set_is_the_platforms_and_reliability_is_not_in_it() -> None:
    """Seven terms, in ``Term``'s own order, on the day-one basis."""

    live = live_terms(LIVE_RULESET, DAY_ONE_ABSENT)
    assert live == tuple(term for term in Term if term is not Term.RELIABILITY)
    assert len(live) == 7


def test_the_gate_is_at_least_half_of_the_live_set() -> None:
    """A fraction and not a count, so it keeps meaning the same thing when a term
    turns on. Today that is four of seven."""

    assert FLOORS.minimum_evidence_fraction == 0.5
    live = live_terms(LIVE_RULESET, DAY_ONE_ABSENT)
    fires = [count for count in range(len(live) + 1) if count / len(live) >= 0.5]
    assert min(fires) == 4


def test_the_gate_moves_nobodys_number() -> None:
    """*A gate, never a score adjustment* — the refused candidate's Fit is
    untouched, which is what makes it a gate rather than a very large dock."""

    thin = modified(
        scored_but_for(
            Term.INTENT_ALIGNMENT,
            Term.AVAILABILITY_OVERLAP,
            Term.PLAYING_STYLE,
            Term.SOCIAL_VIBE,
        )
    )
    refused = admits(thin, LIVE_RULESET, DAY_ONE_ABSENT)
    assert refused.refusal is Refusal.TOO_LITTLE_EVIDENCE
    assert thin.points == pytest.approx(thin.fit.points)


def test_a_person_specific_gap_is_counted_against_them() -> None:
    """Three of seven is under half: an empty grid, no declaration and no tags.

    This is the failure the gate exists for. Renormalisation lifts the survivors
    to a hundred, so a candidate nobody knows anything about can out-score one who
    is merely mediocre — *giving nothing* becoming an advantage at the bar.
    """

    thin = scored_but_for(
        Term.INTENT_ALIGNMENT,
        Term.AVAILABILITY_OVERLAP,
        Term.PLAYING_STYLE,
        Term.SOCIAL_VIBE,
    )
    outcome = admits(modified(thin), LIVE_RULESET, DAY_ONE_ABSENT)
    assert outcome.fired == (Term.LEVEL_FIT, Term.PREDICTED_BALANCE, Term.DISTANCE)
    assert outcome.evidence_fraction == pytest.approx(3 / 7)
    assert outcome.refusal is Refusal.TOO_LITTLE_EVIDENCE


def test_one_more_term_clears_it() -> None:
    """Four of seven, and the same candidate is shown. The gate is a threshold on
    a fraction and the fraction is the thing that moved."""

    thin = scored_but_for(Term.INTENT_ALIGNMENT, Term.PLAYING_STYLE, Term.SOCIAL_VIBE)
    outcome = admits(modified(thin), LIVE_RULESET, DAY_ONE_ABSENT)
    assert outcome.evidence_fraction == pytest.approx(4 / 7)
    assert outcome.admitted


def test_platform_wide_absence_is_never_counted_against_anybody() -> None:
    """Reliability stands down for everybody, so it is nobody's gap.

    Counted the other way, every candidate alive today would carry one automatic
    shortfall — and the gate would be a bar on *how much of the platform is
    built* rather than on how much is known about this person.
    """

    thin = scored_but_for(Term.INTENT_ALIGNMENT, Term.PLAYING_STYLE, Term.SOCIAL_VIBE)
    assert Term.RELIABILITY in thin.degraded_terms
    counted = admits(modified(thin), LIVE_RULESET, DAY_ONE_ABSENT)
    uncounted = admits(modified(thin), LIVE_RULESET, frozenset())
    assert counted.admitted
    assert uncounted.evidence_fraction == pytest.approx(4 / 8)
    assert uncounted.refusal is None
    # Two more gaps and the two readings part company: 3/7 refuses where 3/8 —
    # the same person, with the platform's own hole counted as theirs — refuses
    # for a reason that is not about them at all.
    thinner = scored_but_for(
        Term.INTENT_ALIGNMENT,
        Term.PLAYING_STYLE,
        Term.SOCIAL_VIBE,
        Term.AVAILABILITY_OVERLAP,
    )
    assert admits(modified(thinner), LIVE_RULESET, frozenset()).evidence_fraction < 0.5


def test_the_gate_runs_before_the_bar() -> None:
    """A pairing that produced too little evidence has a Fit that cannot be
    compared to a fixed bar, so recording it as *below the floor* would put the
    wrong population into the floor's own falsifier."""

    thin = scored_but_for(
        Term.INTENT_ALIGNMENT,
        Term.AVAILABILITY_OVERLAP,
        Term.PLAYING_STYLE,
        Term.SOCIAL_VIBE,
    )
    both = modified(thin, applied=-thin.points)
    assert both.points == 0.0
    assert (
        admits(both, LIVE_RULESET, DAY_ONE_ABSENT).refusal
        is Refusal.TOO_LITTLE_EVIDENCE
    )


def test_an_absent_term_no_mode_weights_refuses_to_be_declared_absent() -> None:
    """The register's own check: a term nothing weighs is live nowhere already,
    and naming it absent would be a claim about a provider nobody demands."""

    zeroed = frozenset({Term.LEVEL_FIT})
    assert live_terms(LIVE_RULESET, zeroed) == tuple(
        term for term in Term if term is not Term.LEVEL_FIT
    )
    with pytest.raises(InvariantViolated):
        live_terms(_without(Term.LEVEL_FIT), zeroed)


def _without(term: Term) -> Ruleset:
    """The live ruleset with one term weighted at nothing in both modes."""

    modes = {
        mode: replace(
            rules,
            weights=MappingProxyType(
                {
                    other: (0 if other is term else weight)
                    for other, weight in rules.weights.items()
                }
            ),
        )
        for mode, rules in LIVE_RULESET.modes.items()
    }
    return replace(LIVE_RULESET, modes=MappingProxyType(modes))


def test_the_newcomer_window_excuses_a_gap_and_bends_nothing_else() -> None:
    """*Its one exemption is the newcomer window — and the window bends nothing
    else, not the floor, not a gate, not a block.*

    The exemption is why the window exists: the moment ``player_score`` and
    ``matches`` land, the person with a person-specific gap **is** the newcomer,
    and minimum evidence would become a newcomer exclusion on the day it started
    working. So it is written now, while the gate is inert, because the day it
    starts biting is the day it bites them.
    """

    thin = scored_but_for(
        Term.INTENT_ALIGNMENT,
        Term.AVAILABILITY_OVERLAP,
        Term.PLAYING_STYLE,
        Term.SOCIAL_VIBE,
    )
    assert (
        admits(modified(thin), LIVE_RULESET, DAY_ONE_ABSENT).refusal
        is Refusal.TOO_LITTLE_EVIDENCE
    )
    assert admits(modified(thin), LIVE_RULESET, DAY_ONE_ABSENT, newcomer=True).admitted


def test_the_newcomer_window_does_not_reach_the_floor() -> None:
    """The half that matters more than the exemption: a newcomer below the bar is
    below the bar. A window that could lower a floor would be the relaxation
    ladder's struck rungs arriving under another name."""

    thin = scored_but_for(
        Term.INTENT_ALIGNMENT,
        Term.AVAILABILITY_OVERLAP,
        Term.PLAYING_STYLE,
        Term.SOCIAL_VIBE,
    )
    sunk = modified(thin, applied=FLOORS.quality_floor - thin.points - 1)
    assert (
        admits(sunk, LIVE_RULESET, DAY_ONE_ABSENT, newcomer=True).refusal
        is Refusal.BELOW_QUALITY_FLOOR
    )


# ---------------------------------------------------------------------------
# The one carve-out: a human's own *Let's play*
# ---------------------------------------------------------------------------


def test_an_interest_lift_admits_below_the_bar() -> None:
    """*An interest lift is a human's own yes and outranks the engine's opinion*
    (``docs/adr/0099`` as amended).

    It is the **only** guaranteed inclusion left, and it is not the floor moving:
    the bar is the same integer for everybody, and what clears it here is
    somebody having already said yes to this exact searcher.
    """

    fit = score(searcher(), candidate(), LIVE_RULESET)
    sunk = modified(fit, applied=FLOORS.quality_floor - fit.points - 5)
    assert (
        admits(sunk, LIVE_RULESET, DAY_ONE_ABSENT).refusal
        is Refusal.BELOW_QUALITY_FLOOR
    )

    assert admits(
        sunk, LIVE_RULESET, DAY_ONE_ABSENT, interest_received=True
    ).admitted


def test_an_interest_lift_does_not_reach_the_evidence_gate() -> None:
    """**The two exemptions are disjoint**, and the split is the argument.

    A yes says *I want to play this person*, which outranks the engine's opinion
    of the pairing. It says nothing about whether the platform knows enough to
    have an opinion — and admitting a candidate the engine cannot score would put
    a Fit on the screen that is not comparable to the one beside it.
    """

    thin = scored_but_for(
        Term.INTENT_ALIGNMENT,
        Term.AVAILABILITY_OVERLAP,
        Term.PLAYING_STYLE,
        Term.SOCIAL_VIBE,
    )
    assert (
        admits(
            modified(thin), LIVE_RULESET, DAY_ONE_ABSENT, interest_received=True
        ).refusal
        is Refusal.TOO_LITTLE_EVIDENCE
    )


def test_an_interest_lift_moves_nobodys_number() -> None:
    """It admits, and the Fit it admits is the Fit that was computed.

    The `+14` is a Liveness offset that reorders; the admission is a separate
    decision at stage 5. Neither touches the number on the card, which is what
    lets *Why 78?* keep adding up for a candidate who is only there because
    somebody said yes.
    """

    fit = score(searcher(), candidate(), LIVE_RULESET)
    sunk = modified(fit, applied=FLOORS.quality_floor - fit.points - 5)

    lifted = admits(sunk, LIVE_RULESET, DAY_ONE_ABSENT, interest_received=True)

    assert lifted.admitted
    assert sunk.points < FLOORS.quality_floor
    assert lifted.fired == admits(sunk, LIVE_RULESET, DAY_ONE_ABSENT).fired
