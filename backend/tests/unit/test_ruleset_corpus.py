"""The synthetic corpus: its construction, and the coverage it promises.

The gate itself is a shell check driven against a broken tree
(``make test-ruleset-diff``); what is asserted here is the half a byte
comparison cannot see. A committed artifact proves the corpus **reproduces**;
it cannot prove the corpus is still *exercising* what
``the-replay-harness.md`` §2.1 says it exercises — a generator edit that quietly
stopped producing newcomers would reproduce perfectly for ever and compare two
rulesets over a population neither of them can tell apart.

**Nothing here asserts a rate, a duration or an outcome.** The corpus makes no
absolute claim about anything (ADR-0121), so an assertion about *how many* of
its searches come back empty would be asserting a property of an invented city.
What is asserted is that each stated arm **fires at all**, which is §2.1's own
coverage rule and the reason it is a rule rather than a percentage.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

import pytest

from app.engines.matchfit.v1 import MatchFitV1
from app.modules.matchmaking.infrastructure.rulesets import LIVE_RULESET
from scripts.ruleset_diff.answers import Answers, derive
from scripts.ruleset_diff.population import (
    Density,
    Population,
    as_document,
    generate,
)
from scripts.ruleset_diff.report import compare


@pytest.fixture(scope="module")
def population() -> Population:
    return generate(Density.THIN)


@pytest.fixture(scope="module")
def answers(population: Population) -> Answers:
    """One run of the whole corpus — the same call the ``make`` target makes."""

    return derive(population, LIVE_RULESET, MatchFitV1())


def returned(answers: Answers, *surfaces: str) -> Sequence[Mapping[str, Any]]:
    """Every row those surfaces returned.

    Scoped by surface because a **seated** row is not a shortlist row and does
    not pretend to be: a line-up records who sat down and what their seat was
    worth, where an inclusion reason is a fact about why somebody was in a list
    at all.
    """

    return [
        row
        for record in answers.records
        if record["surface"] in surfaces
        for row in record["returned"]  # type: ignore[union-attr,index]
    ]


# ---------------------------------------------------------------------------
# The generator


def test_the_population_is_a_function_of_its_seed() -> None:
    """Two draws, one population. The committed file is only meaningful if the
    generator is a function — and this is the assertion the byte comparison in
    CI depends on rather than repeats, because CI compares against a *file* and
    this compares two draws in one process."""

    assert as_document(generate(Density.THIN)) == as_document(generate(Density.THIN))


def test_the_two_densities_are_the_ones_the_spec_states() -> None:
    assert Density.THIN.players_per_sport_per_area == 20
    assert Density.DENSE.players_per_sport_per_area == 2_000
    # **100% for the launch market — what a launch factually is.**
    assert Density.THIN.newcomer_fraction == 1.0
    assert Density.DENSE.newcomer_fraction == 0.25


def test_every_drawn_member_sits_inside_the_bounds_the_repository_states(
    population: Population,
) -> None:
    """Uniform wherever the repository supplies no shape, and inside the shape
    where it does: 2–6 tags of the nineteen, at least one of the twenty-one
    cells, a radius the slider can actually be set to."""

    for member in population.members:
        assert 2 <= len(member.tags) <= 6 or member.tail
        assert member.slots
        assert 1 <= member.radius_km <= 50
        assert 1.0 <= member.mu <= 5.0


def test_the_newcomer_fraction_is_a_rule_and_not_a_draw(
    population: Population,
) -> None:
    """At twenty per area a 25% *draw* is five people on a good day and one on a
    bad one. The fraction is a stated property of the corpus, so it is assigned
    by position in a stable order — which is what survives a resize."""

    body = [member for member in population.members if not member.tail]
    assert body, "the corpus has no body to take a fraction of"
    assert all(member.is_newcomer for member in body)


def test_the_adversarial_tail_is_present_and_flagged(
    population: Population,
) -> None:
    """Uniform draws under-sample the rare arms, so the tail makes them fire —
    and every one of them is marked, because the tail is excluded from every
    rate the report prints."""

    tail = [member for member in population.members if member.tail]
    # **Exact, not a floor.** The tail's size is a stated property of the corpus
    # — its rows are excluded from every rate the report prints, so a row
    # arriving or leaving unnoticed changes what the body's percentages are over
    # while the file it is written in still says seven.
    assert len(tail) == 7
    assert {member.handle for member in tail} == {
        "tail-twin",
        "tail-near-twin",
        "tail-far",
        "tail-opposed",
        "tail-newcomer",
        "tail-unseen",
        "tail-wide-week",
    }


# ---------------------------------------------------------------------------
# What the run covers


def test_all_four_surfaces_run(answers: Answers) -> None:
    """§1.1's four surfaces are *different terminal stages*, and pooling their
    rates makes every number meaningless — so a corpus that quietly stopped
    running one would be comparing rulesets over three."""

    assert {record["surface"] for record in answers.records} == {
        "SHORTLIST",
        "LINEUP",
        "FILL_SEATS",
        "DECK",
    }


def test_both_modes_run_on_every_shortlist(answers: Answers) -> None:
    modes = {
        record["mode"]
        for record in answers.records
        if record["surface"] == "SHORTLIST"
    }
    assert modes == {"COMPETITIVE", "FOR_FUN"}


def test_the_three_ledger_inclusion_reasons_each_fire(answers: Answers) -> None:
    """§2.1's coverage rule: `INTEREST_LIFT`, `NEWCOMER_WINDOW` and
    `ZERO_EXPOSURE` each fire for at least one row per density.

    **A rule survives a population resize where a percentage does not** — and
    these are the three rows ADR-0118 §8 makes the *recorded* corpus carry
    forward unrecomputed, so recomputing them is something only this corpus can
    do. A corpus in which none of them fires is a corpus that cannot see a
    change to any of the three.
    """

    reasons = {row["reason"] for row in returned(answers, "SHORTLIST", "DECK")}
    assert {"INTEREST_LIFT", "NEWCOMER_WINDOW", "ZERO_EXPOSURE"} <= reasons


def test_a_deal_reports_its_live_suppressions(answers: Answers) -> None:
    """The one number that tells *your own passes emptied your deck* apart from
    *the pool is empty*, and one nobody can see from any screen because no route
    returns a pass."""

    deals = [
        record for record in answers.records if record["surface"] == "DECK"
    ]
    assert deals
    assert any(record["excluded_by_suppression"] for record in deals)  # type: ignore[index]


def test_the_gate_histogram_is_recorded_whole(answers: Answers) -> None:
    """Every search records the **closed roster** of gate reasons, zeroes
    included: a ruleset that moves *which* gate excluded somebody without moving
    the total is exactly the change a bare ``n_generated`` would hide."""

    counts = answers.records[0]["counts"]
    assert len(counts["excluded_by_gate"]) == 10  # type: ignore[index]


def test_reliabilitys_digest_is_the_empty_one(answers: Answers) -> None:
    """The term has no provider on this platform, so it stands down for
    everybody — printed on the report as an approximation rather than left for a
    reader to discover from a digest that never moves."""

    assert answers.term_readings["RELIABILITY"] == 0


# ---------------------------------------------------------------------------
# The classification, which is derived and never declared


def test_a_corpus_compared_against_itself_is_weight_only(
    answers: Answers,
) -> None:
    """The identity case, asserted because it is the one every green run takes:
    no value moved, so nothing is reordered and nothing crosses the floor."""

    diff = compare(
        {
            "records": list(answers.records),
            "term_values": dict(answers.term_values),
            "term_readings": dict(answers.term_readings),
        },
        answers,
    )
    assert diff.weight_only
    assert diff.moved_terms == ()
    assert diff.verdicts["unchanged"] == diff.searches
    assert diff.top_one_changed == 0


def test_the_tail_is_counted_apart_from_the_body(answers: Answers) -> None:
    """Six invented people may not move a comparison about a population — so the
    tail has its own block and appears in no rate above it."""

    diff = compare(
        {
            "records": list(answers.records),
            "term_values": dict(answers.term_values),
            "term_readings": dict(answers.term_readings),
        },
        answers,
    )
    assert diff.tail_searches > 0
    assert diff.searches + diff.tail_searches == len(answers.records)
