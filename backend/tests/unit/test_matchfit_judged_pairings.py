"""The six judged pairings, re-derived rather than remembered.

``docs/specs/matchmaking/judged-pairings.json`` is the fixture
``the-judged-pairings.md`` is generated from: one searcher, six candidates, held
as **inputs** with a verdict per case, and every term value and every Fit
*derived* (``docs/adr/0122``). It is read **from the spec** rather than copied in
here, because a copied fixture is a fixture that drifts, and the failure it
drifts into is *the tests still pass and the document is now wrong*.

**These are §20.1's scenario fixtures and they assert exact values**, because
that section says what a change to one of them costs: *a diff is a design change
and must be argued for in the pull request.* Approximate assertions would let a
formula move a reading by a tenth and nobody would ever be asked to argue for it.

**The scoring goes through ``scripts.judged_pairings``, which is the harness the
``make`` target and CI run.** Two harnesses would be two answers, and the second
one drifts — so the machine that writes the tables into the documents is the
machine these tests score their cases through, and neither can move without the
other.

Four of the assertions here are the ones the fixture was authored to make, and
they are the ones that cannot be regenerated away:

- **case 2** differs from case 1 by ``shared_cells`` alone, and its Fit falls by
  *exactly* the availability weight — the term's absence costs its weight and not
  a point more;
- **case 6** differs by the candidate's own radius alone, and its Fit is
  **identical**. That identity is the only form in which a machine can assert
  that a named fact moved nothing, and it is the whole of case 6's verdict;
- **case 4**'s intent term is exactly ``0.00`` and it is still shown, above the
  floor, with its reason printed. *Low* is not asserted, because *low* is a claim
  about rank within a population and a fixture has no population;
- **case 3′** is *admitted to scoring* in its own mode and lands **below the
  floor**. Excluded by the gate and merely low are different verdicts, and only
  one of them is what case 3′ is for.

The gates are pinned neutral throughout — no blocks, no holds, both sides
``PREFER_NOT_TO_SAY`` / ``ANY``. These cases test the **scorer**.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.engines.matchfit.core import Term
from app.modules.matchmaking.infrastructure.rulesets import LIVE_RULESET
from scripts.judged_pairings import (
    COLUMNS,
    FIXTURE,
    JUDGED_DOC,
    MODES,
    WEIGHTS_DOC,
    Reading,
    floor_bound,
    read_fixture,
    readings,
    render_bound,
    render_counterfactual,
    render_readings,
    render_totals,
    replace_region,
    score_case,
)
from tests.unit.matchfit_builders import sigma_pair

JUDGED = read_fixture()

#: Every (case, mode) reading the fixture states, flattened so each is its own
#: test — a parametrisation that collapsed the twelve into one would report the
#: first failure and hide the rest.
DERIVED = readings(JUDGED, LIVE_RULESET)

#: The committed reading beside the one this ruleset just derived. The committed
#: half is a generated artifact — ``make gen-judged-pairings`` writes it and CI
#: diffs it — so what these pairs assert is that regenerating would be a no-op,
#: which is the same claim the diff makes and the cheaper place to find it out.
CASES = {str(case["id"]): case for case in JUDGED["cases"]}
RECORDED = [
    (reading, CASES[reading.case_id]["readings"][reading.mode_key])
    for reading in DERIVED
]

IDS = [f"{reading.case_id}-{reading.mode_key}" for reading in DERIVED]


def _by_id(case_id: str, mode_key: str) -> Reading:
    return next(
        reading
        for reading in DERIVED
        if reading.case_id == case_id and reading.mode_key == mode_key
    )


def test_the_fixture_is_where_the_documents_say_it_is() -> None:
    """Loudly rather than skipped.

    A fixture that has moved is a fixture nobody is checking against, and a
    skipped test reports green.
    """

    assert FIXTURE.is_file(), f"the judged pairings are gone from {FIXTURE}"
    assert DERIVED, "the fixture states no readings at all"


@pytest.mark.parametrize(("derived", "recorded"), RECORDED, ids=IDS)
def test_a_judged_pairing_reads_the_values_it_was_judged_on(
    derived: Reading, recorded: dict[str, Any]
) -> None:
    """Every term value, to the four decimals the fixture states them to."""

    for column in COLUMNS:
        assert derived.values[column] == pytest.approx(
            recorded["terms"][column], abs=5e-5
        ), f"{derived.case_id} {derived.mode_key}: {column}"


@pytest.mark.parametrize(("derived", "recorded"), RECORDED, ids=IDS)
def test_a_judged_pairing_scores_the_fit_it_was_judged_on(
    derived: Reading, recorded: dict[str, Any]
) -> None:
    """And the number the whole map is calibrated against.

    Day one reliability stands down, so the live basis is **seven terms
    renormalised** — ×100/87 competitive, ×100/91 for fun. That basis is what
    every judged reading, the quality floor and every cross reading were computed
    on, and it is the number to reproduce.
    """

    assert derived.fit.degraded_terms == (Term.RELIABILITY,)
    assert derived.fit.points == pytest.approx(recorded["fit"], abs=5e-3)


@pytest.mark.parametrize(("derived", "recorded"), RECORDED, ids=IDS)
def test_a_judged_pairing_renormalises_onto_the_recorded_basis(
    derived: Reading, recorded: dict[str, Any]
) -> None:
    """The seven renormalised weights are the fixture's own ``basis`` block."""

    weights = {term.term: term.weight for term in derived.fit.terms}
    basis = JUDGED["basis"][derived.mode_key]
    for column, term in COLUMNS.items():
        assert weights[term] == pytest.approx(basis[column], abs=5e-4)


@pytest.mark.parametrize(("derived", "recorded"), RECORDED, ids=IDS)
def test_a_judged_pairing_reads_the_forecast_it_was_judged_on(
    derived: Reading, recorded: dict[str, Any]
) -> None:
    """The balance forecast behind the normalised reading, as a percentage.

    Recorded because the term normalises across its own clamp: a reading of
    ``0.16`` says nothing about what was forecast until the clamp bounds are
    named, and moving a bound would move every balance reading at once while
    leaving the percentage where it was.
    """

    assert derived.balance_pct == pytest.approx(recorded["balance_pct"], abs=5e-3)


def test_the_combined_uncertainty_is_the_one_the_fixture_names() -> None:
    """σ_pair is RacketSkill's combination and is never re-derived in the engine.

    Asserted here rather than taken on trust because every balance reading above
    rests on it: on day one σ is a constant for everybody, so a wrong combination
    would move all twelve Fits together and look like a weight problem.
    """

    stated = sorted({recorded["sigma_pair"] for _, recorded in RECORDED})
    assert stated == pytest.approx(
        [sigma_pair(JUDGED["searcher"]["sigma"], JUDGED["searcher"]["sigma"])],
        abs=5e-5,
    )


def test_losing_the_availability_term_costs_exactly_its_weight() -> None:
    """Case 2 against case 1 — one input apart, and the difference is the weight.

    Overlap is evidence a game can be *arranged*, never a proposed time, so its
    absence costs the term's weight and **not a point more**: no second dock, no
    stand-down, no renormalisation. The measured zero is the whole charge.
    """

    for mode_key in MODES:
        full = _by_id("1", mode_key).fit.points
        none = _by_id("2", mode_key).fit.points
        assert full - none == pytest.approx(
            JUDGED["basis"][mode_key]["avail"], abs=5e-4
        )


def test_the_candidates_own_radius_moves_nothing_at_all() -> None:
    """Case 6 against case 1 — **identical**, and that is the verdict.

    The searcher sitting outside the candidate's ring is a Liveness dock and
    never a gate: somebody who set a small radius is not refusing to be found.
    An identity is the only form in which a machine can assert that a named fact
    moved nothing.
    """

    for mode_key in MODES:
        assert _by_id("6", mode_key).fit.points == _by_id("1", mode_key).fit.points


def test_the_candidates_own_radius_is_still_printed() -> None:
    """Moved nothing, and said so — the fact is evidence and never a term."""

    outside = {
        term.evidence
        for term in _by_id("6", "comp").fit.terms
        if term.term is Term.DISTANCE
    }
    assert [evidence.outside_their_radius for evidence in outside] == [True]  # type: ignore[union-attr]
    inside = {
        term.evidence
        for term in _by_id("1", "comp").fit.terms
        if term.term is Term.DISTANCE
    }
    assert [evidence.outside_their_radius for evidence in inside] == [False]  # type: ignore[union-attr]


def test_the_case_that_exists_to_test_intent_reads_exactly_zero() -> None:
    """Case 4: exceptional on everything, and opposite on the one thing.

    *Low* is unachievable and the fixture does not claim it — a candidate who
    loses only the intent term scores 80.3, the second-highest number in the set.
    What is checkable is what is asserted: the term reads exactly ``0.00``, the
    candidate is still shown, and the concern is printed.
    """

    reading = _by_id("4", "comp")
    assert reading.values["intent"] == 0.0
    assert reading.is_shown
    assert reading.fit.points > LIVE_RULESET.floors.quality_floor
    assert Term.INTENT_ALIGNMENT in reading.fit.concerns


@pytest.mark.parametrize(
    ("case_id", "mode_key"), [("3'-comp", "comp"), ("3'-fun", "fun")]
)
def test_case_three_prime_is_admitted_to_scoring_and_lands_below_the_floor(
    case_id: str, mode_key: str
) -> None:
    """Case 3′ is refused by the **floor**, and never by the gate.

    Case 3 was excluded by the level gate, which makes it a fixture about
    generation rather than about scoring; case 3′ replaces it precisely so the
    floor has something to be read off. So both halves are the assertion:
    ``Δμ < LEVEL_TOL_mode`` — ADR-0103 gates at ``Δμ ≥ LEVEL_TOL_mode``, so this
    pairing is admitted and does produce a Fit — and that Fit is below the floor.

    **It is two pairings and not one**, because the tolerance is mode-relative:
    at Δμ 0.54 the candidate is a hair inside competitive's gate and nowhere near
    for-fun's, and at Δμ 0.89 competitive has already excluded them and there is
    no number to record.
    """

    reading = _by_id(case_id, mode_key)
    tolerance = LIVE_RULESET.modes[reading.mode].level_tolerance
    assert reading.delta_mu < tolerance, (
        f"{case_id} is outside {mode_key}'s gate, so it is excluded before it is "
        f"scored and the floor is not what refuses it"
    )
    assert not reading.is_shown
    assert reading.fit.points < LIVE_RULESET.floors.quality_floor


def test_socially_blank_is_a_measured_zero_and_never_a_stand_down() -> None:
    """Case 1's tags fire nothing at all, in either column, in either mode.

    Both players hold tags in both columns' domains and no row fires, so both tag
    terms read the measured **0.20** — *different, not incompatible*.
    """

    for mode_key in MODES:
        reading = _by_id("1", mode_key)
        assert reading.values["style"] == pytest.approx(0.20)
        assert reading.values["vibe"] == pytest.approx(0.20)
        assert Term.PLAYING_STYLE not in reading.fit.degraded_terms
        assert Term.SOCIAL_VIBE not in reading.fit.degraded_terms


def test_standing_the_tag_columns_down_would_beat_declaring_everything() -> None:
    """The counterfactual that makes the measured zero a decision.

    Scored with both columns stood down and renormalised over the five terms
    that remain, socially blank case 1 outscores case 4 — *everything
    exceptional* — in competitive, and by more than the whole social vibe weight.
    **Declaring nothing would beat declaring everything**, which is the
    renormalisation pathology the evidence gate and the measured 0.20 exist to
    refuse, argued in prose since `the-five-numbers.md` §1 and never before
    given a number.
    """

    blank = _by_id("1", "comp")
    exceptional = _by_id("4", "comp")
    assert blank.blank_points > exceptional.fit.points
    assert blank.blank_points > blank.fit.points
    assert _by_id("1", "fun").blank_points > _by_id("1", "fun").fit.points


def test_the_quality_floor_still_sits_inside_the_bound_the_six_leave() -> None:
    """``max(Fit | not shown) < QUALITY_FLOOR ≤ min(Fit | shown)``.

    `the-five-numbers.md` §1 defines the floor by six judged cases rather than by
    an integer, and `ranking-weights.md` §11 makes turning a term on a ruleset
    release that re-runs them. That is an inequality, and this is it — the one
    thing about the fixture a regeneration cannot make true again.
    """

    bound = floor_bound(DERIVED, LIVE_RULESET)
    assert bound.configured == LIVE_RULESET.floors.quality_floor
    assert bound.holds, (
        f"QUALITY_FLOOR = {bound.configured} is outside "
        f"{bound.highest_hidden:.2f} < floor <= {bound.lowest_shown:.2f}"
    )
    assert bound.highest_hidden == pytest.approx(_by_id("3'-fun", "fun").fit.points)
    assert bound.lowest_shown == pytest.approx(_by_id("5", "comp").fit.points)


def test_the_floor_bound_refuses_a_fixture_with_nothing_on_one_side() -> None:
    """A floor read off cases that are all shown is bounded by nothing at all.

    Refused rather than reported as holding, because a vacuous pass is the exact
    shape of failure the re-derivation exists to prevent.
    """

    from scripts.judged_pairings import Unreadable

    shown_only = [reading for reading in DERIVED if reading.is_shown]
    with pytest.raises(Unreadable):
        floor_bound(shown_only, LIVE_RULESET)


@pytest.mark.parametrize(
    ("document", "region", "body"),
    [
        (JUDGED_DOC, "judged-readings", lambda: render_readings(DERIVED)),
        (JUDGED_DOC, "blank-counterfactual", lambda: render_counterfactual(DERIVED)),
        (WEIGHTS_DOC, "judged-totals", lambda: render_totals(DERIVED)),
    ],
    ids=["judged-readings", "blank-counterfactual", "judged-totals"],
)
def test_a_generated_table_reproduces_from_the_fixture(
    document: Any, region: str, body: Any
) -> None:
    """The documents' tables are what this ruleset derives, byte for byte.

    CI asserts the same thing by regenerating and diffing, which is the gate.
    This is the fast local half: a formula change fails here, in the suite
    somebody is already running, naming the table rather than a shell exit code.
    """

    text = document.read_text(encoding="utf-8")
    assert replace_region(text, region, body(), document) == text


@pytest.mark.parametrize(
    "document", [JUDGED_DOC, WEIGHTS_DOC], ids=["judged", "weights"]
)
def test_both_documents_print_the_same_re_derived_bound(document: Any) -> None:
    """One bound, in two documents, and neither of them typed by hand."""

    text = document.read_text(encoding="utf-8")
    body = render_bound(floor_bound(DERIVED, LIVE_RULESET))
    assert replace_region(text, "floor-bound", body, document) == text


def test_the_case_a_search_would_score_is_the_case_the_tables_print() -> None:
    """The harness scores through ``score``, and nothing else scores here.

    Named because the tables and these assertions would agree with each other
    perfectly while both disagreeing with the engine, if the harness had ever
    grown its own arithmetic. It has not: this re-scores one case through the
    same entry point and asserts the recorded reading is that call's answer.
    """

    rescored = score_case(JUDGED, CASES["5"], "comp")
    assert rescored.points == _by_id("5", "comp").fit.points
