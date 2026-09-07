"""Renormalisation, ranking and concerns — what turns eight readings into a number.

The property this file exists for: **the renormalised weights sum to a hundred
for every subset of live terms**, in either mode. It is asserted over the whole
space rather than over the subsets today's inputs happen to reach, because three
of the eight cannot stand down on today's data and a renormalisation only ever
exercised on the reachable ones is one that breaks the day reliability turns on.

Two hundred and fifty-five subsets by two modes is a **finite** space, so it is
enumerated rather than sampled: *for every subset* is a claim a machine can make
completely here, and a generator drawing a hundred of them would be a weaker
statement dressed as a stronger one.
"""

from __future__ import annotations

import dataclasses
from itertools import combinations

import pytest

from app.engines.matchfit.core import DegradedReason, SearchMode, Term
from app.engines.matchfit.ruleset import WEIGHT_TOTAL
from app.bootstrap.composition import build_match_fit_engine
from app.engines.matchfit.scoring import MatchFit
from app.engines.matchfit.v1 import (
    ENGINE_VERSION,
    MatchFitV1,
    renormalised_weights,
    score,
)
from app.engines.matchfit.v1 import fit as fit_module
from app.engines.matchfit.scoring import Fit, StoodDown
from app.kernel import InvariantViolated
from app.modules.matchmaking.infrastructure.rulesets import LIVE_RULESET
from app.modules.player_profile.domain.play_intent import PlayIntent
from app.modules.player_profile.domain.social_tags import SocialTag
from tests.unit.matchfit_builders import candidate, searcher

#: Every non-empty subset of the eight terms — 255 of them, in a stable order.
SUBSETS = [
    live for size in range(1, len(Term) + 1) for live in combinations(list(Term), size)
]


@pytest.mark.parametrize("mode", list(SearchMode))
def test_the_renormalised_weights_sum_to_a_hundred_for_every_subset(
    mode: SearchMode,
) -> None:
    """The property, over the whole space and not over a sample of it."""

    weights = LIVE_RULESET.modes[mode].weights
    for live in SUBSETS:
        shares = renormalised_weights(weights, live)
        assert sum(shares.values()) == pytest.approx(WEIGHT_TOTAL, abs=1e-9), live


@pytest.mark.parametrize("mode", list(SearchMode))
def test_renormalisation_preserves_every_pair_of_terms_relative_weight(
    mode: SearchMode,
) -> None:
    """Redistribution, not reweighting.

    A term standing down must not change what the surviving terms are worth
    *relative to each other* — otherwise a missing Player Score would quietly
    re-rank the whole city, and nothing about anybody changed.
    """

    weights = LIVE_RULESET.modes[mode].weights
    for live in SUBSETS:
        shares = renormalised_weights(weights, live)
        for first, second in combinations(live, 2):
            assert shares[first] * weights[second] == pytest.approx(
                shares[second] * weights[first], abs=1e-9
            )


def test_a_renormalisation_over_no_weight_at_all_is_refused() -> None:
    """Not a Fit of zero — no Fit. Returning a number here would be the invented
    zero every stand-down rule in the engine exists to refuse."""

    with pytest.raises(InvariantViolated, match="no weight at all"):
        renormalised_weights(LIVE_RULESET.modes[SearchMode.COMPETITIVE].weights, ())


def test_a_stood_down_term_redistributes_its_weight_and_never_shrinks_the_fit() -> None:
    """Two candidates identical except that one has not declared an intent.

    The silent one is scored over six terms rather than seven, and every reading
    it does have is worth proportionally more. A candidate who says nothing is
    not docked for saying nothing — which is what makes *declaring the opposite*
    the strictly more expensive answer.
    """

    facts = dict(
        tags=(SocialTag.PLAYS_TO_WIN.value, SocialTag.HERE_TO_COMPETE.value),
        distance_km=2.0,
    )
    silent = score(searcher(tags=facts["tags"]), candidate(**facts), LIVE_RULESET)
    declared = score(
        searcher(tags=facts["tags"]),
        candidate(declared_intent=PlayIntent.NO_PREFERENCE.value, **facts),
        LIVE_RULESET,
    )
    assert StoodDown(
        term=Term.INTENT_ALIGNMENT, reason=DegradedReason.NOTHING_FROM_THEM
    ) in silent.degraded_terms
    assert Term.INTENT_ALIGNMENT not in {
        stood.term for stood in declared.degraded_terms
    }
    assert sum(term.weight for term in silent.terms) == pytest.approx(WEIGHT_TOTAL)
    for term in silent.terms:
        matching = next(other for other in declared.terms if other.term is term.term)
        assert term.weight > matching.weight


def test_the_degraded_terms_are_the_renormalisation_basis_and_travel_with_the_fit() -> (
    None
):
    """Without them the number is uninterpretable a year later.

    ``Fit`` renormalises **per comparison**, so which terms fired *is* the
    reading — and the basis is a field on the answer rather than a line in a log
    for exactly that reason.
    """

    fit = score(searcher(), candidate(), LIVE_RULESET)
    stood = {entry.term for entry in fit.degraded_terms}
    assert stood | {term.term for term in fit.terms} == set(Term)
    assert stood & {term.term for term in fit.terms} == set()
    # Nobody declared, nobody has a Player Score, and neither holds a tag: four
    # of the eight are honestly absent on this pairing.
    assert stood == {
        Term.INTENT_ALIGNMENT,
        Term.RELIABILITY,
        Term.PLAYING_STYLE,
        Term.SOCIAL_VIBE,
    }
    # **In `Term`s own order**, which is what makes the recorded reasons
    # index-alignable against it a year later rather than a set read twice.
    assert [entry.term for entry in fit.degraded_terms] == [
        term for term in Term if term in stood
    ]


def test_the_engine_never_authors_the_platforms_own_gap() -> None:
    """``score`` is not told which providers exist, and could not say.

    Reliability stands down here because the null object returns no reading,
    which the term honestly reports as *nothing from them* — a sentence about a
    person, written from an accident of a wiring choice. Restating it is
    ``floor.attributed``'s job, one layer out, where ``absent`` lives.
    """

    fit = score(searcher(), candidate(), LIVE_RULESET)
    assert DegradedReason.NOT_YET_ON_THIS_PLATFORM not in {
        entry.reason for entry in fit.degraded_terms
    }


def test_the_reasons_are_ranked_by_contribution_and_the_cap_is_not_the_engines() -> (
    None
):
    """The ordering is arithmetic and is not the client's.

    Every term that fired comes back — the card renders three of it and *Why 78?*
    renders all of it, over data it already holds. Capping here would put two
    payload shapes behind one concept.
    """

    fit = score(searcher(), candidate(), LIVE_RULESET)
    contributions = [term.contribution for term in fit.terms]
    assert contributions == sorted(contributions, reverse=True)
    assert len(fit.terms) == len(Term) - len(fit.degraded_terms)
    assert fit.points == pytest.approx(sum(contributions))


def test_a_tie_between_two_terms_breaks_on_a_declaration_and_never_on_a_set() -> None:
    """Determinism is a set-iteration problem, and it is asserted rather than assumed.

    Driven against a ruleset that weights the two tag terms **equally**, so the
    tie is exact rather than a float coincidence: both columns read the same
    measured 0.20 on the same pairing, so the two contributions are identical
    bit for bit and only the tie-break can separate them. Playing style is
    declared before social vibe, so it comes first — on every process and
    whatever ``PYTHONHASHSEED`` is.
    """

    tags = (SocialTag.QUIET_AND_FOCUSED.value, SocialTag.HERE_TO_COMPETE.value)
    mine = (SocialTag.PLAYS_TO_WIN.value, SocialTag.STAYS_FOR_A_DRINK.value)
    comp = LIVE_RULESET.modes[SearchMode.COMPETITIVE]
    level = comp.weights[Term.PLAYING_STYLE]
    tied = dataclasses.replace(
        LIVE_RULESET,
        modes={
            **LIVE_RULESET.modes,
            SearchMode.COMPETITIVE: dataclasses.replace(
                comp,
                weights={**comp.weights, Term.SOCIAL_VIBE: level},
            ),
        },
    )
    fit = score(searcher(tags=mine), candidate(tags=tags), tied)
    columns = [
        term
        for term in fit.terms
        if term.term in {Term.PLAYING_STYLE, Term.SOCIAL_VIBE}
    ]
    assert len(columns) == 2
    assert columns[0].contribution == columns[1].contribution
    assert [term.term for term in columns] == [Term.PLAYING_STYLE, Term.SOCIAL_VIBE]


def test_the_contribution_is_the_renormalised_weight_times_the_value() -> None:
    """The breakdown adds up, and it has to: *Why 78?* is the moment the
    product's central claim is tested, and a breakdown that does not add up is
    the claim failing."""

    fit = score(searcher(), candidate(), LIVE_RULESET)
    for term in fit.terms:
        assert term.contribution == pytest.approx(term.weight * term.value)


def test_both_version_stamps_ride_on_the_answer() -> None:
    """The engine version says how the maths works; the ruleset version says what
    the numbers were. Two stamps, because moving a weight leaves the first
    untouched and that is the whole point of there being two."""

    fit = score(searcher(), candidate(), LIVE_RULESET)
    assert fit.engine_version == ENGINE_VERSION
    assert fit.ruleset_version == LIVE_RULESET.version


def test_the_version_satisfies_the_protocol_a_module_will_depend_on() -> None:
    """**One ``Protocol`` per engine** — a module depends on the abstraction and
    never on a concrete version, so swapping ``v1`` for ``v2`` is a line in the
    composition root rather than an edit at every call site.

    Asserted rather than assumed, because a Protocol nothing is checked against
    is a Protocol that drifts from its only implementation in silence: the class
    keeps working, and the abstraction quietly stops describing it.
    """

    engine = MatchFitV1()
    assert isinstance(engine, MatchFit)
    assert engine.version == ENGINE_VERSION
    through_the_protocol: MatchFit = engine
    assert through_the_protocol.score(
        searcher=searcher(), candidate=candidate(), ruleset=LIVE_RULESET
    ) == score(searcher(), candidate(), LIVE_RULESET)


def test_the_composition_root_chooses_the_version_and_nowhere_else_does() -> None:
    """The choice of implementation is one line, in the one place that makes it."""

    assert isinstance(build_match_fit_engine(), MatchFit)


# ---------------------------------------------------------------------------
# Concerns
# ---------------------------------------------------------------------------


def _concerns_of(mode: SearchMode) -> Fit:
    """A pairing that is perfect on everything except the two tag columns.

    Both hold tags in both domains and nothing fires, so both terms read the
    measured 0.20 — the same pairing, the same two readings, in the two modes.
    """

    tags = (SocialTag.QUIET_AND_FOCUSED.value, SocialTag.HERE_TO_COMPETE.value)
    mine = (SocialTag.PLAYS_TO_WIN.value, SocialTag.STAYS_FOR_A_DRINK.value)
    return score(
        searcher(mode=mode, tags=mine),
        candidate(
            tags=tags,
            declared_intent=(
                PlayIntent.COMPETITIVE.value
                if mode is SearchMode.COMPETITIVE
                else PlayIntent.FOR_FUN.value
            ),
        ),
        LIVE_RULESET,
    )


def test_a_concern_is_judged_on_the_points_it_costs_and_so_reads_by_mode() -> None:
    """The same weakness, warned about in one mode and not the other.

    A social vibe of 0.20 costs under four points of a competitive match and
    nearly twenty of a friendly, and only one of those is worth a line on a card.
    Judging on **points forgone** rather than on the raw value makes that fall out
    of the weights instead of needing a second table — and it is why the
    threshold lives where the weights and the curves are rather than in a client.
    """

    competitive = _concerns_of(SearchMode.COMPETITIVE)
    friendly = _concerns_of(SearchMode.FOR_FUN)
    values = {term.term: term.value for term in competitive.terms}
    assert values[Term.SOCIAL_VIBE] == pytest.approx(0.20)
    assert Term.SOCIAL_VIBE not in competitive.concerns
    assert Term.SOCIAL_VIBE in friendly.concerns


def test_concerns_are_ranked_by_what_they_cost_and_are_not_capped() -> None:
    """A card shows one, *Why 78?* shows all — and the cap is the client's,
    because capping here would throw away exactly the rows that explain a low Fit
    on the screen built to explain it."""

    fit = _concerns_of(SearchMode.FOR_FUN)
    forgone = {term.term: term.weight * (1.0 - term.value) for term in fit.terms}
    ranked = [forgone[term] for term in fit.concerns]
    assert ranked == sorted(ranked, reverse=True)
    assert all(cost >= LIVE_RULESET.explanation.concern_points for cost in ranked)


def test_a_term_that_stood_down_is_never_a_concern() -> None:
    """It produced no reading, so there is nothing to be weak about.

    *We did not look* and *we looked and it is poor* are different statements and
    they travel in different fields — a stood-down term is in the basis, which is
    the honest place to say so.
    """

    fit = score(searcher(), candidate(), LIVE_RULESET)
    assert set(fit.concerns) & {stood.term for stood in fit.degraded_terms} == set()


def test_a_candidate_with_no_evidence_at_all_is_refused_rather_than_scored(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A Fit over no evidence is not a low Fit — it is not a Fit.

    It is **unreachable on today's inputs**, which is exactly why it is driven
    here rather than left as a guard nobody has watched fire: level fit and
    distance read facts every candidate in the index has, so the day this raises
    is the day one of those quietly stopped being true. Every term is made to
    stand down at once, and the refusal names the candidate — because a Fit that
    came back as a number here would be the invented zero every stand-down rule
    in this engine exists to refuse.
    """

    monkeypatch.setattr(fit_module, "read_terms", lambda *_: tuple(None for _ in Term))
    with pytest.raises(InvariantViolated, match="every term of Fit stood down"):
        score(searcher(), candidate(player_id="nobody"), LIVE_RULESET)
