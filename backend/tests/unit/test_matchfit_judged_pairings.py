"""The six judged pairings, re-derived rather than remembered.

``docs/specs/matchmaking/judged-pairings.json`` is the fixture
``the-judged-pairings.md`` is generated from: one searcher, six candidates, every
term value and every Fit stated in advance of any code. It is read **from the
spec** rather than copied in here, because a copied fixture is a fixture that
drifts, and the failure it drifts into is *the tests still pass and the document
is now wrong*.

**This is not the replay harness and not the release-time floor re-derivation** —
those are somebody else's ticket, with ``make`` targets and a corpus. This is the
narrow thing that ticket cannot do for us today: proof that the eight terms
compute the numbers the map says they compute, on inputs somebody judged by hand.

Two of the six are one-line assertions against case 1, and they are the two worth
saying out loud:

- **case 2** differs by ``shared_cells`` alone, and its Fit falls by *exactly* the
  availability weight — the term's absence costs its weight and not a point more;
- **case 6** differs by the candidate's own radius alone, and its Fit is
  **identical**. That identity is the only form in which a machine can assert
  that a named fact moved nothing, and it is the whole of case 6's verdict.

The gates are pinned neutral throughout — no blocks, no holds, both sides
``PREFER_NOT_TO_SAY`` / ``ANY``. These cases test the **scorer**, which is
exactly what this ticket builds.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from app.engines.matchfit import core as engine_package
from app.engines.matchfit.core import SearchMode, Term
from app.engines.matchfit.scorable import GridCell
from app.engines.matchfit.scoring import Fit
from app.engines.matchfit.v1 import score
from app.modules.matchmaking.infrastructure.rulesets import LIVE_RULESET
from app.modules.player_profile.domain.availability import DayPart
from tests.unit.matchfit_builders import (
    FOUR_CELLS,
    candidate,
    cells,
    searcher,
    sigma_pair,
)

#: The fixture, located through a module inside ``backend/`` rather than by this
#: file's own depth, so moving the tests does not silently point the read at
#: nothing. It is read **from the spec** and never copied here: a copied fixture
#: drifts, and the failure it drifts into is *the tests still pass and the
#: document is now wrong*.
FIXTURE = (
    Path(engine_package.__file__).parents[4]
    / "docs"
    / "specs"
    / "matchmaking"
    / "judged-pairings.json"
)

#: The fixture's own column names against the terms they read. The fixture is
#: product's document and its spellings are its own; this is the one place the
#: two vocabularies are mapped, so a renamed column is one edit and a loud one.
COLUMNS = {
    "level": Term.LEVEL_FIT,
    "balance": Term.PREDICTED_BALANCE,
    "intent": Term.INTENT_ALIGNMENT,
    "avail": Term.AVAILABILITY_OVERLAP,
    "style": Term.PLAYING_STYLE,
    "distance": Term.DISTANCE,
    "vibe": Term.SOCIAL_VIBE,
}

MODES = {"comp": SearchMode.COMPETITIVE, "fun": SearchMode.FOR_FUN}


def _fixture() -> dict[str, Any]:
    # Loudly rather than skipped. A fixture that has moved is a fixture nobody is
    # checking against, and a skipped test reports green.
    assert FIXTURE.is_file(), f"the judged pairings are gone from {FIXTURE}"
    loaded: dict[str, Any] = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return loaded


JUDGED = _fixture()

#: Every (case, mode) reading the fixture states, flattened so each is its own
#: test — a parametrisation that collapsed the twelve into one would report the
#: first failure and hide the rest.
READINGS = [
    (case["id"], mode, case, reading)
    for case in JUDGED["cases"]
    for mode, reading in case["readings"].items()
]


def _scored(case: dict[str, Any], mode: str) -> Fit:
    """One judged case, built through the same fenced types a search builds."""

    theirs = case["candidate"]
    searcher_facts = JUDGED["searcher"]
    return score(
        searcher(
            mu=searcher_facts["mu"],
            sigma=searcher_facts["sigma"],
            mode=MODES[mode],
            tags=tuple(searcher_facts["tags"]),
            grid=cells(*_grid(searcher_facts["grid_cells"])),
            radius_km=searcher_facts["radius_km"],
        ),
        candidate(
            player_id=f"case-{case['id']}",
            mu=theirs["mu"],
            sigma=theirs["sigma"],
            against_sigma=searcher_facts["sigma"],
            declared_intent=case["intent"],
            tags=tuple(theirs["tags"]),
            grid=_their_grid(theirs["shared_cells"]),
            radius_km=theirs["radius_km"],
            distance_km=theirs["km"],
        ),
        LIVE_RULESET,
    )


def _grid(count: int) -> list[tuple[int, DayPart]]:
    """``count`` cells of the searcher's four, in the grid's own order."""

    assert count <= len(FOUR_CELLS), f"the fixture ticks {count} of four cells"
    return [(int(cell.day), DayPart[cell.part]) for cell in FOUR_CELLS[:count]]


#: A cell the searcher did **not** tick, so a candidate sharing none of theirs
#: still has a week.
UNSHARED = (7, DayPart.AFTERNOON)


def _their_grid(shared: int) -> tuple[GridCell, ...]:
    """The candidate's own week: ``shared`` of the searcher's cells, plus one.

    The extra cell is the whole reason this helper exists rather than a slice.
    ``shared_cells: 0`` in the fixture means *they share none of your times*,
    which is a **measurement** and scores zero; a candidate with no grid at all
    is *we do not know when they play*, which stands the term down and
    renormalises its weight onto the other six. Those two are different readings
    and the fixture judged the first — so a builder that spelled zero overlap as
    an empty week would quietly test the other one, and case 2's whole assertion
    is about what zero overlap costs.
    """

    return cells(*_grid(shared), UNSHARED)


@pytest.mark.parametrize(
    ("case_id", "mode", "case", "reading"),
    READINGS,
    ids=[f"{case_id}-{mode}" for case_id, mode, _, _ in READINGS],
)
def test_a_judged_pairing_reads_the_values_it_was_judged_on(
    case_id: str, mode: str, case: dict[str, Any], reading: dict[str, Any]
) -> None:
    """Every term value, to the four decimals the fixture states them to."""

    fit = _scored(case, mode)
    values = {term.term: term.value for term in fit.terms}
    for column, term in COLUMNS.items():
        assert term in values, f"{case_id} {mode}: {term.value} stood down"
        assert values[term] == pytest.approx(reading["terms"][column], abs=5e-5), (
            f"{case_id} {mode}: {term.value}"
        )


@pytest.mark.parametrize(
    ("case_id", "mode", "case", "reading"),
    READINGS,
    ids=[f"{case_id}-{mode}" for case_id, mode, _, _ in READINGS],
)
def test_a_judged_pairing_scores_the_fit_it_was_judged_on(
    case_id: str, mode: str, case: dict[str, Any], reading: dict[str, Any]
) -> None:
    """And the number the whole map is calibrated against.

    Day one reliability stands down, so the live basis is **seven terms
    renormalised** — ×100/87 competitive, ×100/91 for fun. That basis is what
    every judged reading, the quality floor and every cross reading were computed
    on, and it is the number to reproduce.
    """

    fit = _scored(case, mode)
    assert fit.degraded_terms == (Term.RELIABILITY,)
    assert fit.points == pytest.approx(reading["fit"], abs=5e-3)


@pytest.mark.parametrize(
    ("case_id", "mode", "case", "reading"),
    READINGS,
    ids=[f"{case_id}-{mode}" for case_id, mode, _, _ in READINGS],
)
def test_a_judged_pairing_renormalises_onto_the_recorded_basis(
    case_id: str, mode: str, case: dict[str, Any], reading: dict[str, Any]
) -> None:
    """The seven renormalised weights are the fixture's own ``basis`` block."""

    fit = _scored(case, mode)
    weights = {term.term: term.weight for term in fit.terms}
    for column, term in COLUMNS.items():
        assert weights[term] == pytest.approx(JUDGED["basis"][mode][column], abs=5e-4)


def test_the_combined_uncertainty_is_the_one_the_fixture_names() -> None:
    """σ_pair is RacketSkill's combination and is never re-derived in the engine.

    Asserted here rather than taken on trust because every balance reading above
    rests on it: on day one σ is a constant for everybody, so a wrong combination
    would move all twelve Fits together and look like a weight problem.
    """

    stated = sorted({reading["sigma_pair"] for _, _, _, reading in READINGS})
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

    by_id = {case["id"]: case for case in JUDGED["cases"]}
    for mode in MODES:
        full = _scored(by_id["1"], mode).points
        none = _scored(by_id["2"], mode).points
        assert full - none == pytest.approx(JUDGED["basis"][mode]["avail"], abs=5e-4)


def test_the_candidates_own_radius_moves_nothing_at_all() -> None:
    """Case 6 against case 1 — **identical**, and that is the verdict.

    The searcher sitting outside the candidate's ring is a Liveness dock and
    never a gate: somebody who set a small radius is not refusing to be found.
    An identity is the only form in which a machine can assert that a named fact
    moved nothing.
    """

    by_id = {case["id"]: case for case in JUDGED["cases"]}
    for mode in MODES:
        assert _scored(by_id["6"], mode).points == _scored(by_id["1"], mode).points


def test_the_candidates_own_radius_is_still_printed() -> None:
    """Moved nothing, and said so — the fact is evidence and never a term."""

    by_id = {case["id"]: case for case in JUDGED["cases"]}
    outside = {
        term.evidence
        for term in _scored(by_id["6"], "comp").terms
        if term.term is Term.DISTANCE
    }
    assert [evidence.outside_their_radius for evidence in outside] == [True]  # type: ignore[union-attr]
    inside = {
        term.evidence
        for term in _scored(by_id["1"], "comp").terms
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

    case = next(case for case in JUDGED["cases"] if case["id"] == "4")
    fit = _scored(case, "comp")
    values = {term.term: term.value for term in fit.terms}
    assert values[Term.INTENT_ALIGNMENT] == 0.0
    assert fit.points > LIVE_RULESET.floors.quality_floor
    assert Term.INTENT_ALIGNMENT in fit.concerns


def test_socially_blank_is_a_measured_zero_and_never_a_stand_down() -> None:
    """Case 1's tags fire nothing at all, in either column, in either mode.

    Both players hold tags in both columns' domains and no row fires, so both tag
    terms read the measured **0.20** — *different, not incompatible*. Standing
    them down instead would score case 1 at 92.9 competitive against case 4's
    80.3: **declaring nothing would beat declaring everything by twelve points**,
    which is the renormalisation pathology the measured zero exists to prevent.
    """

    case = next(case for case in JUDGED["cases"] if case["id"] == "1")
    for mode in MODES:
        fit = _scored(case, mode)
        values = {term.term: term.value for term in fit.terms}
        assert values[Term.PLAYING_STYLE] == pytest.approx(0.20)
        assert values[Term.SOCIAL_VIBE] == pytest.approx(0.20)
        assert Term.PLAYING_STYLE not in fit.degraded_terms
        assert Term.SOCIAL_VIBE not in fit.degraded_terms
