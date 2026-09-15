"""The ruleset: what it refuses to load, and the facts the live one pins.

Two kinds of test, and the split is deliberate.

**Refusals** drive a deliberately broken ruleset through the validator and assert
it goes red — the idiom this repository already holds three times over
(``make test-drift``, ``make test-poetry-pin``, ``make test-hooks``), on the
stated reason that *a guardrail that silently stops matching is worse than none,
because you stop watching for it.*

**Pinned facts** assert the numbers that other documents were argued from. A
weight is free to move — that is the whole point of a ruleset — so these do not
pin weights. They pin the things a weight change would *break*: the counts the
tag matrix's coverage argument rests on, the silent liveness roster
``docs/adr/0123`` closes, and the two version stamps.
"""

from __future__ import annotations

import ast
import dataclasses
import importlib
from pathlib import Path
from types import MappingProxyType

import pytest

from app.core.config import Environment
from app.engines.matchfit.core import (
    K_CEILING,
    ChallengeLoad,
    ClashSeverity,
    EvidenceKind,
    FamiliarityReading,
    LivenessSignal,
    Modifier,
    RelaxationRung,
    ReliabilityStrand,
    SearchMode,
    Seat,
    TagColumn,
    TagRelationshipKind,
    Term,
)
from app.engines.matchfit.ruleset import (
    ChallengeLoadRung,
    ModeRules,
    PointRange,
    Ruleset,
    SignalBound,
    TagRelationship,
    validate_ruleset,
)
from app.engines.matchfit.v1 import ENGINE_VERSION
from app.engines.matchfit.v1 import engine as engine_version_module
from app.kernel import InvariantViolated
from app.modules.matchmaking.infrastructure import rulesets as ruleset_registry
from app.modules.matchmaking.infrastructure.rulesets import (
    LIVE_RULESET,
    LIVE_RULESET_VERSION,
    RULESETS,
)
from app.modules.matchmaking.infrastructure.rulesets import (
    r2026_08_26_a as dataset_module,
)
from app.modules.player_profile.domain.play_intent import PlayIntent
from app.modules.player_profile.domain.social_tags import SocialTag

#: ``backend/app``, derived from a module inside it rather than from this file's
#: own depth, so moving the tests does not silently point the walk at nothing.
APP_ROOT = Path(dataset_module.__file__).parents[4]

# ---------------------------------------------------------------------------
# The two stamps


def test_the_live_ruleset_is_named_dated_and_registered_under_its_own_name() -> None:
    assert LIVE_RULESET.version == LIVE_RULESET_VERSION
    assert LIVE_RULESET.released_on == "2026-09-15"
    assert RULESETS[LIVE_RULESET_VERSION] is LIVE_RULESET


def test_a_released_ruleset_cannot_be_edited() -> None:
    """*Immutable once released* — a change is a new name, never an edit.

    Held by frozen dataclasses and read-only mappings rather than by discipline,
    because the thing it protects is a search recorded a year ago: if the numbers
    behind ``2026.09.08-a`` can move, then every stamp naming it is a lie about
    what ran.
    """

    with pytest.raises(dataclasses.FrozenInstanceError):
        LIVE_RULESET.version = "2026.08.27-a"  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        LIVE_RULESET.floors.quality_floor = 52  # type: ignore[misc]
    with pytest.raises(TypeError):
        LIVE_RULESET.modes[SearchMode.COMPETITIVE].weights[Term.LEVEL_FIT] = 40  # type: ignore[index]
    with pytest.raises(AttributeError):
        LIVE_RULESET.tags.relationship_matrix.append(None)  # type: ignore[attr-defined]


def test_a_ruleset_whose_date_disagrees_with_its_name_refuses_to_load() -> None:
    """Two spellings of one fact, so the pair is checked rather than trusted."""

    with pytest.raises(InvariantViolated, match="disagrees with its name"):
        validate_ruleset(dataclasses.replace(LIVE_RULESET, released_on="2026-08-27"))


@pytest.mark.parametrize("version", ["2026.08.26", "2026-08-26-a", "2026.8.26-a", "a"])
def test_a_ruleset_version_is_a_date_and_a_letter(version: str) -> None:
    """The letter is what makes a second release on one day a new dataset."""

    with pytest.raises(InvariantViolated):
        validate_ruleset(dataclasses.replace(LIVE_RULESET, version=version))


def test_the_engine_version_is_not_the_ruleset_version() -> None:
    """Two stamps, and moving a number leaves one of them untouched.

    They are asserted apart because the failure mode is somebody deriving one
    from the other, after which a weight release would silently claim the maths
    changed.
    """

    assert ENGINE_VERSION == "matchfit-v1"
    assert ENGINE_VERSION != LIVE_RULESET.version


def test_the_four_environments_resolve_the_same_ruleset(monkeypatch) -> None:
    """`local`, `development`, `staging` and `production` run the same numbers.

    **The modules are genuinely re-executed under each name**, because
    ``LIVE_RULESET`` is resolved at import: a plain re-``import`` would hit
    ``sys.modules`` and hand back the same object four times, which is a
    tautology a ruleset that *did* read ``APP_ENV`` would sail through. The
    reload is what makes the loop able to fail.

    A weight is not a setting. It is the product's opinion about who a player
    should meet, which is behaviour a domain test can observe — so
    ``docs/adr/0028``'s rule applies to it without exception.
    """

    assert set(Environment) == {
        Environment.LOCAL,
        Environment.DEVELOPMENT,
        Environment.STAGING,
        Environment.PRODUCTION,
    }

    resolved = set()
    for environment in Environment:
        monkeypatch.setenv("APP_ENV", environment.value)
        importlib.reload(engine_version_module)
        importlib.reload(dataset_module)
        registry = importlib.reload(ruleset_registry)
        resolved.add(
            (registry.LIVE_RULESET.version, engine_version_module.ENGINE_VERSION)
        )

    assert len(resolved) == 1

    # And left as it was found: the reloaded modules are the ones every other
    # test holds references into.
    monkeypatch.setenv("APP_ENV", Environment.LOCAL.value)
    importlib.reload(engine_version_module)
    importlib.reload(dataset_module)
    importlib.reload(ruleset_registry)


@pytest.mark.parametrize(
    "package",
    [
        APP_ROOT / "engines" / "matchfit",
        APP_ROOT / "modules" / "matchmaking" / "infrastructure" / "rulesets",
    ],
    ids=["engine", "ruleset store"],
)
def test_nothing_that_resolves_a_ruleset_can_read_configuration(package: Path) -> None:
    """The reload above catches an import-time read; this catches every other one.

    ``import-linter`` fences the engines layer off ``app.core.config`` already,
    but the ruleset **store** is a module's infrastructure and is on the outside
    of that contract — so the claim is asserted over the source of both halves
    rather than half of it.
    """

    sources = sorted(package.rglob("*.py"))
    assert sources, package
    # Imports and names rather than raw text: the modules *discuss* `APP_ENV` in
    # their docstrings, at length and on purpose, and a walk that could not tell
    # a sentence about a rule from a breach of it would be deleted the first time
    # somebody documented the rule properly. Nothing can read an environment
    # without importing something that can.
    forbidden_imports = {"os", "app.core.config", "pydantic_settings"}
    forbidden_names = {"get_settings", "Settings", "Environment", "environ", "getenv"}
    for source in sources:
        tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert (
                        alias.name.split(".")[0] not in forbidden_imports
                        and alias.name not in forbidden_imports
                    ), f"{source.name} imports {alias.name}"
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                assert (
                    module.split(".")[0] not in forbidden_imports
                    and module not in forbidden_imports
                ), f"{source.name} imports from {module}"
                for alias in node.names:
                    assert alias.name not in forbidden_names, (
                        f"{source.name} imports {alias.name}"
                    )
            elif isinstance(node, ast.Attribute):
                assert node.attr not in forbidden_names, (
                    f"{source.name} reaches for {node.attr}"
                )


# ---------------------------------------------------------------------------
# Weights


@pytest.mark.parametrize("mode", list(SearchMode))
def test_every_mode_weights_every_term_and_every_strand(mode: SearchMode) -> None:
    rules = LIVE_RULESET.modes[mode]
    assert set(rules.weights) == set(Term)
    assert sum(rules.weights.values()) == 100
    assert set(rules.strand_weights) == set(ReliabilityStrand)
    assert sum(rules.strand_weights.values()) == 100


def test_a_term_weight_vector_that_does_not_sum_to_a_hundred_refuses_to_load() -> None:
    competitive = LIVE_RULESET.modes[SearchMode.COMPETITIVE]
    heavier = dict(competitive.weights)
    heavier[Term.LEVEL_FIT] += 1
    with pytest.raises(InvariantViolated, match="sums to 101"):
        validate_ruleset(_with_mode(dataclasses.replace(competitive, weights=heavier)))


def test_a_term_missing_from_a_weight_vector_refuses_to_load() -> None:
    """A missing key would renormalise away and read as a term that stood down —
    the one thing this engine is careful to keep distinguishable from a term
    that scored badly."""

    competitive = LIVE_RULESET.modes[SearchMode.COMPETITIVE]
    short = {
        term: weight
        for term, weight in competitive.weights.items()
        if term is not Term.SOCIAL_VIBE
    }
    short[Term.LEVEL_FIT] += competitive.weights[Term.SOCIAL_VIBE]
    with pytest.raises(InvariantViolated, match="term weights"):
        validate_ruleset(_with_mode(dataclasses.replace(competitive, weights=short)))


def test_a_strand_with_no_observation_bar_refuses_to_load() -> None:
    """**A bar per strand, and the mapping is exhaustive** (``docs/adr/0160``).

    A strand nobody set a bar for would enter a reading on its first observation
    — a *we have seen one thing about you* published as a verdict — and nothing
    else in the pipeline would notice. So the field was a single ``int`` and is
    now a mapping, and the mapping is checked rather than defaulted.
    """

    reliability = LIVE_RULESET.reliability
    short = {
        strand: bar
        for strand, bar in reliability.min_observations.items()
        if strand is not ReliabilityStrand.ANSWERS_RESULTS
    }
    with pytest.raises(InvariantViolated, match="must name every strand"):
        validate_ruleset(
            dataclasses.replace(
                LIVE_RULESET,
                reliability=dataclasses.replace(
                    reliability, min_observations=short
                ),
            )
        )


def test_an_observation_bar_below_one_refuses_to_load() -> None:
    """A bar of nought is a strand with no bar at all, spelled as a number."""

    reliability = LIVE_RULESET.reliability
    zeroed = dict(reliability.min_observations)
    zeroed[ReliabilityStrand.SHOWS_UP] = 0
    with pytest.raises(InvariantViolated, match="SHOWS_UP"):
        validate_ruleset(
            dataclasses.replace(
                LIVE_RULESET,
                reliability=dataclasses.replace(
                    reliability, min_observations=zeroed
                ),
            )
        )


def test_the_for_fun_free_band_must_sit_inside_its_own_tolerance() -> None:
    """A band at the tolerance leaves the curve no range to fall through."""

    for_fun = LIVE_RULESET.modes[SearchMode.FOR_FUN]
    assert for_fun.free_band is not None and for_fun.free_band < for_fun.level_tolerance
    with pytest.raises(InvariantViolated, match="free band"):
        validate_ruleset(
            _with_mode(
                dataclasses.replace(for_fun, free_band=for_fun.level_tolerance),
                mode=SearchMode.FOR_FUN,
            )
        )


def test_the_tag_terms_may_not_outrank_a_noticeably_better_level_match() -> None:
    """*Six well-chosen tags must not outrank a good level match* — as an
    inequality rather than an intention, because an intention does not survive a
    weight release.

    Both tag terms clamp to ``[0, 1]``, so their largest possible contribution is
    exactly ``w_style + w_vibe`` and the rule needs no knowledge of the curve or
    the matrix.
    """

    competitive = LIVE_RULESET.modes[SearchMode.COMPETITIVE]
    assert competitive.tag_stuffing_margin == 0.30

    stuffed = dict(competitive.weights)
    moved = stuffed[Term.LEVEL_FIT] - 20
    stuffed[Term.LEVEL_FIT] = 20
    stuffed[Term.SOCIAL_VIBE] += moved
    with pytest.raises(InvariantViolated, match="can outrank"):
        validate_ruleset(
            _with_mode(
                dataclasses.replace(competitive, weights=MappingProxyType(stuffed))
            )
        )


def test_for_fun_has_no_tag_stuffing_constraint() -> None:
    """Deliberate, and the absence is the decision. In a friendly the tags are
    *supposed* to outrank level, and constraining them would delete the inversion
    the whole vector is built around."""

    assert LIVE_RULESET.modes[SearchMode.FOR_FUN].tag_stuffing_margin is None


def test_competitive_has_no_free_band() -> None:
    """Every tenth of a point of gap is priced from zero in a competitive game."""

    assert LIVE_RULESET.modes[SearchMode.COMPETITIVE].free_band is None


# ---------------------------------------------------------------------------
# The tag matrix


def test_the_matrix_is_thirty_seven_rows_over_eighteen_matches() -> None:
    """The counts the coverage argument rests on: eighteen matches, twelve
    complements, seven clashes."""

    matrix = LIVE_RULESET.tags.relationship_matrix
    assert len(matrix) == 37
    by_kind = {kind: 0 for kind in TagRelationshipKind}
    for row in matrix:
        by_kind[row.kind] += 1
    assert by_kind == {
        TagRelationshipKind.MATCH: 18,
        TagRelationshipKind.COMPLEMENT: 12,
        TagRelationshipKind.CLASH: 7,
    }


def test_the_column_domains_are_derived_and_are_ten_and_twelve() -> None:
    """Derived from the rows, never declared, so they re-derive when product
    edits one. A tag may sit in both; a tag with no row is in neither."""

    style = LIVE_RULESET.tags.column_domain(TagColumn.STYLE)
    vibe = LIVE_RULESET.tags.column_domain(TagColumn.VIBE)
    assert len(style) == 10
    assert len(vibe) == 12
    assert (
        SocialTag.TALKS_THROUGH_THE_MATCH.value in style
        and SocialTag.TALKS_THROUGH_THE_MATCH.value in vibe
    )
    assert SocialTag.OPEN_TO_MEET_SOMEONE.value not in style | vibe


def test_a_match_row_is_one_tag_against_itself_and_carries_no_strength() -> None:
    with pytest.raises(InvariantViolated, match="not a tag against itself"):
        validate_ruleset(
            _with_extra_row(
                TagRelationship(
                    a=SocialTag.PLAYS_TO_WIN.value,
                    b=SocialTag.QUIET_AND_FOCUSED.value,
                    kind=TagRelationshipKind.MATCH,
                    column=TagColumn.STYLE,
                    modes=tuple(SearchMode),
                    seats=tuple(Seat),
                )
            )
        )


def test_a_tag_may_not_take_two_match_rows() -> None:
    with pytest.raises(InvariantViolated, match="more than one match row"):
        validate_ruleset(
            _with_extra_row(
                TagRelationship(
                    a=SocialTag.PLAYS_TO_WIN.value,
                    b=SocialTag.PLAYS_TO_WIN.value,
                    kind=TagRelationshipKind.MATCH,
                    column=TagColumn.VIBE,
                    modes=tuple(SearchMode),
                    seats=tuple(Seat),
                )
            )
        )


def test_two_rows_about_one_pair_must_have_disjoint_scopes() -> None:
    """Two rows are how *far worse as partners than as opponents* is said without
    a second severity field. Overlapping scopes would make them two answers to
    one question."""

    with pytest.raises(InvariantViolated, match="overlap on"):
        validate_ruleset(
            _with_extra_row(
                TagRelationship(
                    a=SocialTag.TALKS_THROUGH_THE_MATCH.value,
                    b=SocialTag.QUIET_AND_FOCUSED.value,
                    kind=TagRelationshipKind.CLASH,
                    column=TagColumn.STYLE,
                    modes=(SearchMode.FOR_FUN,),
                    seats=(Seat.PARTNER,),
                    severity=ClashSeverity.MILD,
                )
            )
        )


def test_a_complement_may_not_sit_below_the_default_strength() -> None:
    """A complement product is not confident about should not be a row."""

    with pytest.raises(InvariantViolated, match="complement strength"):
        validate_ruleset(
            _with_extra_row(
                TagRelationship(
                    a=SocialTag.SHARES_A_LIFT.value,
                    b=SocialTag.QUIET_AND_FOCUSED.value,
                    kind=TagRelationshipKind.COMPLEMENT,
                    column=TagColumn.VIBE,
                    modes=tuple(SearchMode),
                    seats=tuple(Seat),
                    strength=0.5,
                )
            )
        )


def test_a_complement_may_not_be_worth_more_than_a_match() -> None:
    """Parity is the most an editorial claim can be worth against two people's
    agreement (``docs/adr/0115``)."""

    with pytest.raises(InvariantViolated, match="complement strength"):
        validate_ruleset(
            _with_extra_row(
                TagRelationship(
                    a=SocialTag.SHARES_A_LIFT.value,
                    b=SocialTag.QUIET_AND_FOCUSED.value,
                    kind=TagRelationshipKind.COMPLEMENT,
                    column=TagColumn.VIBE,
                    modes=tuple(SearchMode),
                    seats=tuple(Seat),
                    strength=1.2,
                )
            )
        )


def test_a_mild_clash_is_milder_than_a_real_one_and_both_fit_under_the_cap() -> None:
    severities = LIVE_RULESET.tags.clash_severities
    assert severities[ClashSeverity.MILD] < severities[ClashSeverity.REAL]
    assert max(severities.values()) <= LIVE_RULESET.tags.clash_cap


def test_the_familiarity_reading_map_covers_all_three_readings() -> None:
    readings = set(LIVE_RULESET.tags.familiarity_reading_map.values())
    assert readings == set(FamiliarityReading)


# ---------------------------------------------------------------------------
# Liveness


def test_the_silent_roster_is_exactly_two_signals_and_its_reachable_net() -> None:
    """``docs/adr/0123``'s roster test. A third silent signal is a decision, not
    a row — and the reachable net is what makes the upper clamp unreachable
    today, which is true of the roster and not of the rule."""

    liveness = LIVE_RULESET.liveness
    assert liveness.silent_signals() == (
        LivenessSignal.PREVIOUS_DECLINE,
        LivenessSignal.EXPOSURE_ADJUSTMENT,
    )
    assert liveness.reachable_silent_net() == PointRange(minimum=-12, maximum=6)


def test_a_full_inbox_never_sinks_a_candidate_past_their_own_lets_play() -> None:
    """A human's own ask outranks the engine's opinion of that human's
    popularity, and the two numbers are anchored to each other rather than
    chosen."""

    liveness = LIVE_RULESET.liveness
    load = liveness.signals[LivenessSignal.CHALLENGE_LOAD]
    interest = liveness.signals[LivenessSignal.INTEREST_RECEIVED]
    assert load.points.minimum + interest.points.maximum > 0
    assert (
        load.points.minimum
        == liveness.signals[LivenessSignal.RECIPROCAL_ASYMMETRY].points.minimum
    )

    sunk = dict(liveness.signals)
    sunk[LivenessSignal.CHALLENGE_LOAD] = SignalBound(
        PointRange(-14, 0), printable=True
    )
    with pytest.raises(InvariantViolated, match="full inbox"):
        validate_ruleset(
            dataclasses.replace(
                LIVE_RULESET,
                liveness=dataclasses.replace(liveness, signals=MappingProxyType(sunk)),
            )
        )


def test_a_signal_may_not_reach_past_the_offsets_own_bounds() -> None:
    liveness = LIVE_RULESET.liveness
    reaching = dict(liveness.signals)
    reaching[LivenessSignal.RECENT_ACTIVITY] = SignalBound(
        PointRange(-40, 4), printable=True
    )
    with pytest.raises(InvariantViolated, match="reaches past the offset"):
        validate_ruleset(
            dataclasses.replace(
                LIVE_RULESET,
                liveness=dataclasses.replace(
                    liveness, signals=MappingProxyType(reaching)
                ),
            )
        )


def test_the_interest_lift_must_print() -> None:
    """``docs/adr/0099``'s carve-out: a player is owed the reason they were shown
    somebody who asked for them."""

    liveness = LIVE_RULESET.liveness
    silenced = dict(liveness.signals)
    silenced[LivenessSignal.INTEREST_RECEIVED] = SignalBound(
        PointRange(14, 14), printable=False
    )
    with pytest.raises(InvariantViolated, match="interest lift must print"):
        validate_ruleset(
            dataclasses.replace(
                LIVE_RULESET,
                liveness=dataclasses.replace(
                    liveness, signals=MappingProxyType(silenced)
                ),
            )
        )


def test_the_full_inbox_sink_is_fourteen_fours_three_rungs() -> None:
    """§14.4's thresholds, adopted **whole** by ``docs/adr/0125``.

    Only the third's effect changed — a 24-hour withholding became the sink's own
    floor — so the depths and the two shallower docks are the input document's
    own, unedited. Each rung names the coarse code it prints, so a threshold
    moving cannot silently re-point a code at a different depth.
    """

    rungs = LIVE_RULESET.liveness.challenge_load_rungs
    assert [(rung.at_least, rung.points) for rung in rungs] == [
        (3, -4),
        (5, -8),
        (8, -12),
    ]
    assert [rung.prints for rung in rungs] == [
        ChallengeLoad.SOME,
        ChallengeLoad.BUSY,
        ChallengeLoad.FULL,
    ]


@pytest.mark.parametrize(
    ("rungs", "match"),
    [
        pytest.param((), "no rungs", id="empty"),
        pytest.param(
            (
                ChallengeLoadRung(at_least=5, points=-4, prints=ChallengeLoad.SOME),
                ChallengeLoadRung(at_least=3, points=-8, prints=ChallengeLoad.BUSY),
                ChallengeLoadRung(at_least=8, points=-12, prints=ChallengeLoad.FULL),
            ),
            "not deepest last",
            id="out-of-order",
        ),
        pytest.param(
            (
                ChallengeLoadRung(at_least=3, points=-8, prints=ChallengeLoad.SOME),
                ChallengeLoadRung(at_least=5, points=-4, prints=ChallengeLoad.BUSY),
                ChallengeLoadRung(at_least=8, points=-12, prints=ChallengeLoad.FULL),
            ),
            "costs no more",
            id="deeper-costs-less",
        ),
        pytest.param(
            (
                ChallengeLoadRung(at_least=3, points=-4, prints=ChallengeLoad.SOME),
                ChallengeLoadRung(at_least=5, points=-8, prints=ChallengeLoad.SOME),
                ChallengeLoadRung(at_least=8, points=-12, prints=ChallengeLoad.FULL),
            ),
            "print the same code",
            id="duplicate-code",
        ),
        pytest.param(
            (
                ChallengeLoadRung(at_least=3, points=-4, prints=ChallengeLoad.SOME),
                ChallengeLoadRung(at_least=5, points=-6, prints=ChallengeLoad.BUSY),
                ChallengeLoadRung(at_least=8, points=-8, prints=ChallengeLoad.FULL),
            ),
            "a bound nothing can reach",
            id="short-of-the-bound",
        ),
        pytest.param(
            (
                ChallengeLoadRung(at_least=3, points=-4, prints=ChallengeLoad.SOME),
                ChallengeLoadRung(at_least=5, points=-8, prints=ChallengeLoad.BUSY),
                ChallengeLoadRung(at_least=8, points=-20, prints=ChallengeLoad.FULL),
            ),
            "reaches past the signal",
            id="past-the-bound",
        ),
    ],
)
def test_a_malformed_full_inbox_sink_refuses_to_load(
    rungs: tuple[ChallengeLoadRung, ...], match: str
) -> None:
    """The ladder is checked rather than trusted, in both directions.

    A sink that stopped short of its own bound would leave a number nothing can
    produce — the shape of a bound somebody widened and forgot to spend — and one
    that reached past it would sink a candidate further than the roster says any
    signal may.
    """

    with pytest.raises(InvariantViolated, match=match):
        validate_ruleset(
            dataclasses.replace(
                LIVE_RULESET,
                liveness=dataclasses.replace(
                    LIVE_RULESET.liveness, challenge_load_rungs=rungs
                ),
            )
        )


def test_the_reciprocal_dock_is_priced_proportionately_and_not_flat() -> None:
    """The struck radius dock's replacement: a slope over the shortfall past the
    tolerance, saturating at the signal's own bound."""

    liveness = LIVE_RULESET.liveness
    assert liveness.asymmetry_tolerance == 12
    assert liveness.asymmetry_slope == 0.5
    with pytest.raises(InvariantViolated, match="asymmetry slope"):
        validate_ruleset(
            dataclasses.replace(
                LIVE_RULESET,
                liveness=dataclasses.replace(liveness, asymmetry_slope=0.0),
            )
        )


def test_the_notice_threshold_does_two_jobs_and_is_one_constant() -> None:
    """It is the movement that owes an explanation *and* the silent stack's
    budget. Two constants could drift apart in a ruleset edit and break the
    printing guarantee silently."""

    assert LIVE_RULESET.liveness.move_notice == 6


# ---------------------------------------------------------------------------
# Modifiers, group, floors, shape, relaxation, interest


def test_the_reliability_penalty_is_derived_and_sits_outside_the_budget() -> None:
    """A stack of small positives must never lift somebody over a recent
    no-show, so the smallest penalty that keeps the promise is budget + 1 — and
    defining it that way means it moves by itself if the budget does."""

    modifiers = LIVE_RULESET.modifiers
    assert modifiers.floor_breach_penalty == -(modifiers.budget + 1) == -11
    assert Modifier.RELIABILITY_FLOOR_BREACH not in modifiers.ranges


def test_the_newcomer_absorption_cap_keeps_its_rule_and_refuses_its_integer() -> None:
    """With no players there is no distribution to sit it in, and the modifier it
    bounds cannot fire, so any integer would be untestable."""

    assert LIVE_RULESET.modifiers.newcomer_absorption_cap is None


def test_the_candidate_cap_may_not_exceed_the_engine_side_ceiling() -> None:
    """The one number that can destroy the line-up latency budget, which is why
    it may not ship as *just configuration*."""

    assert LIVE_RULESET.group.k == K_CEILING
    with pytest.raises(InvariantViolated, match="exceeds the engine-side ceiling"):
        validate_ruleset(
            dataclasses.replace(
                LIVE_RULESET,
                group=dataclasses.replace(LIVE_RULESET.group, k=K_CEILING + 1),
            )
        )


@pytest.mark.parametrize("mode", list(SearchMode))
def test_the_group_objective_weights_every_term_in_every_mode(mode: SearchMode) -> None:
    weights = LIVE_RULESET.group.weights[mode]
    assert sum(weights.values()) == 100


def test_the_floors_and_the_two_shape_constants() -> None:
    """The floor is the bar; the shape constants only say where a list stops.
    They are separate blocks for that reason."""

    assert LIVE_RULESET.floors.quality_floor == 44
    assert LIVE_RULESET.floors.min_shortlist == 5
    assert LIVE_RULESET.floors.minimum_evidence_fraction == 0.5
    assert LIVE_RULESET.shape.shortlist_max == 20
    assert LIVE_RULESET.shape.deck_deal_max == 10


def test_the_ladder_is_the_enums_order_and_not_ruleset_data() -> None:
    """``max_rung`` and the ordered-rung list are struck. *Times before distance*
    and *there is no third radius rung* are arguments, so a release may move how
    far a rung reaches and may not add one."""

    assert tuple(RelaxationRung) == (
        RelaxationRung.TIMES,
        RelaxationRung.RADIUS_NEAR,
        RelaxationRung.RADIUS_FAR,
    )
    assert not hasattr(LIVE_RULESET.relaxation, "rungs")


def test_the_radius_rungs_stop_at_double() -> None:
    relaxation = LIVE_RULESET.relaxation
    assert relaxation.radius_multipliers[RelaxationRung.RADIUS_NEAR] == 1.5
    assert relaxation.radius_multipliers[RelaxationRung.RADIUS_FAR] == 2.0
    assert RelaxationRung.TIMES not in relaxation.radius_multipliers


def test_a_radius_rung_that_reaches_no_further_than_the_last_refuses_to_load() -> None:
    """A rung duplicating another rung's radius is not offered twice."""

    relaxation = LIVE_RULESET.relaxation
    flat = dict(relaxation.radius_multipliers)
    flat[RelaxationRung.RADIUS_FAR] = 1.5
    with pytest.raises(InvariantViolated, match="do not widen in order"):
        validate_ruleset(
            dataclasses.replace(
                LIVE_RULESET,
                relaxation=dataclasses.replace(
                    relaxation, radius_multipliers=MappingProxyType(flat)
                ),
            )
        )


def test_the_four_interest_numbers_and_the_near_miss_depth() -> None:
    interest = LIVE_RULESET.interest
    assert interest.ttl_days == 21
    assert interest.outstanding_cap_per_sport == 20
    assert interest.pass_suppress_days == 30
    assert interest.deck_cool_off_days == 30
    assert LIVE_RULESET.telemetry.near_miss_recorded == 10


def test_the_cool_off_is_a_row_the_older_releases_never_knew_and_say_nought_about() -> (
    None
):
    """``2026.09.15-a`` is the one release that moves it (``docs/adr/0169``
    §6). The two before it were edited to say nought — *no window after a
    court*, which is what their decks did — on the precedent the sixth strand
    set: a shape change is not a number moving, and a released dataset says
    the honest thing about a row that did not exist when it shipped."""

    assert RULESETS["2026.08.26-a"].interest.deck_cool_off_days == 0
    assert RULESETS["2026.09.08-a"].interest.deck_cool_off_days == 0
    assert RULESETS["2026.09.15-a"].interest.deck_cool_off_days == 30
    with pytest.raises(InvariantViolated, match="cool-off"):
        validate_ruleset(
            dataclasses.replace(
                LIVE_RULESET,
                interest=dataclasses.replace(
                    LIVE_RULESET.interest, deck_cool_off_days=-1
                ),
            )
        )


# ---------------------------------------------------------------------------
# Intent, distance and the concern bar — the three blocks the scorer reads


def test_the_intent_table_is_six_cells_and_the_two_zeros_are_not_symmetric() -> None:
    """A competitive searcher meeting a declared friendly reads nothing at all;
    a for-fun searcher meeting a declared competitor still reads something.

    A competitor will play a friendly, and the reverse ruins the evening for one
    of them — so the asymmetry is the claim, and pinning it here is what stops a
    later release flattening it by accident.
    """

    alignment = LIVE_RULESET.intent.alignment
    assert sum(len(row) for row in alignment.values()) == 6
    competitive = alignment[SearchMode.COMPETITIVE]
    friendly = alignment[SearchMode.FOR_FUN]
    assert competitive[PlayIntent.FOR_FUN.value] == 0.00
    assert friendly[PlayIntent.COMPETITIVE.value] > 0.00
    # The honest middle is nearly as good as a match, in both modes and equally.
    assert (
        competitive[PlayIntent.NO_PREFERENCE.value]
        == friendly[PlayIntent.NO_PREFERENCE.value]
        == 0.85
    )


def test_an_intent_table_that_prices_different_declarations_per_mode_refuses() -> None:
    """*Six cells* is a rectangle, not two lists the same length today.

    A declaration priced in one mode and absent from the other would stand the
    term down for a player who answered the question — but only on one tab, for
    a reason nobody wrote down.
    """

    row = dict(LIVE_RULESET.intent.alignment[SearchMode.FOR_FUN])
    row["SOMETHING_ELSE"] = row.pop(PlayIntent.NO_PREFERENCE.value)
    with pytest.raises(InvariantViolated, match="price different declarations"):
        validate_ruleset(_with_intent_row(SearchMode.FOR_FUN, row))


def test_an_intent_cell_outside_the_terms_own_range_refuses_to_load() -> None:
    row = dict(LIVE_RULESET.intent.alignment[SearchMode.COMPETITIVE])
    row[PlayIntent.NO_PREFERENCE.value] = 1.4
    with pytest.raises(InvariantViolated, match=r"outside \[0, 1\]"):
        validate_ruleset(_with_intent_row(SearchMode.COMPETITIVE, row))


def test_a_mode_must_name_the_declaration_it_reads_as_its_own_evening() -> None:
    """``aligned`` is a fact about two declarations and never a threshold read
    off a weight — the two enums share two spellings today and that is a
    coincidence the arithmetic is not allowed to lean on."""

    with pytest.raises(InvariantViolated, match="does not price"):
        validate_ruleset(
            dataclasses.replace(
                LIVE_RULESET,
                intent=dataclasses.replace(
                    LIVE_RULESET.intent,
                    same_evening=MappingProxyType(
                        {
                            SearchMode.COMPETITIVE: "A_THIRD_THING",
                            SearchMode.FOR_FUN: PlayIntent.FOR_FUN.value,
                        }
                    ),
                ),
            )
        )


def test_two_modes_may_not_read_the_same_declaration_as_their_own() -> None:
    """It would make one mode's alignment unreachable and the other's zero
    unwritable — two tabs claiming the same evening."""

    with pytest.raises(InvariantViolated, match="claim the same declaration"):
        validate_ruleset(
            dataclasses.replace(
                LIVE_RULESET,
                intent=dataclasses.replace(
                    LIVE_RULESET.intent,
                    same_evening=MappingProxyType(
                        {mode: PlayIntent.FOR_FUN.value for mode in SearchMode}
                    ),
                ),
            )
        )


def test_the_distance_curve_runs_from_seventy_percent_of_the_ring_to_115() -> None:
    """Both are fractions of the searcher's own ring and never kilometres: a ten
    kilometre searcher and a fifty kilometre one each said what far means to
    them, and a constant in kilometres would overrule one of them."""

    assert LIVE_RULESET.distance.full_marks_within == 0.70
    assert LIVE_RULESET.distance.zero_at == 1.15


def test_a_distance_curve_that_does_not_descend_refuses_to_load() -> None:
    with pytest.raises(InvariantViolated, match="does not descend"):
        validate_ruleset(_with_distance(full_marks_within=1.20, zero_at=1.15))


def test_a_distance_curve_reaching_zero_inside_the_ring_refuses_to_load() -> None:
    """The hard cut at the ring is a gate. A curve reaching zero at or inside it
    would charge for that gate a second time, in a term."""

    with pytest.raises(InvariantViolated, match="inside the ring"):
        validate_ruleset(_with_distance(full_marks_within=0.50, zero_at=1.00))


def test_the_concern_bar_sits_at_or_above_the_lightest_term_on_the_live_basis() -> None:
    """Anchored rather than picked.

    The smallest weight any term carries on the day-one renormalised basis is
    social vibe's 4.6 competitive, so a bar under it would let a term raise a
    warning about a shortfall it cannot produce even by reading zero — and a
    warning line that fires on nothing has stopped being a warning.
    """

    weights = LIVE_RULESET.modes[SearchMode.COMPETITIVE].weights
    live = {
        term: weight for term, weight in weights.items() if term is not Term.RELIABILITY
    }
    basis = sum(live.values())
    lightest = min(weight * 100 / basis for weight in live.values())
    assert LIVE_RULESET.explanation.concern_points >= lightest


def test_a_concern_bar_of_nothing_refuses_to_load() -> None:
    """Every term with any shortfall at all would raise a warning, which is a
    caption rather than a concern."""

    with pytest.raises(InvariantViolated, match="concern bar"):
        validate_ruleset(
            dataclasses.replace(
                LIVE_RULESET,
                explanation=dataclasses.replace(
                    LIVE_RULESET.explanation, concern_points=0
                ),
            )
        )


# ---------------------------------------------------------------------------
# Emittable evidence


def test_every_weighted_term_can_emit_its_variant() -> None:
    """Reliability is weighted and merely has no provider yet, so its variant is
    published and unfilled rather than absent."""

    assert LIVE_RULESET.emittable_evidence_kinds() == set(EvidenceKind)


def test_a_term_weighted_at_nothing_in_both_modes_emits_nothing() -> None:
    """Distance rather than level fit, because zeroing level fit divides by a
    weight the tag-stuffing inequality reads and the ruleset refuses to load —
    which is the inequality working, in a test that is about something else."""

    silent = validate_ruleset(_zeroed(Term.DISTANCE))
    assert EvidenceKind.DISTANCE not in silent.emittable_evidence_kinds()


# ---------------------------------------------------------------------------
# Helpers


def _zeroed(term: Term) -> Ruleset:
    """The live ruleset with one term at nothing, its weight given to intent.

    Given away rather than dropped, because a vector that no longer sums to a
    hundred fails for a reason that has nothing to do with what the caller is
    asking about.
    """

    modes = {}
    for mode, rules in LIVE_RULESET.modes.items():
        weights = dict(rules.weights)
        weights[Term.INTENT_ALIGNMENT] += weights[term]
        weights[term] = 0
        modes[mode] = dataclasses.replace(rules, weights=MappingProxyType(weights))
    return dataclasses.replace(LIVE_RULESET, modes=MappingProxyType(modes))


def _with_mode(rules: ModeRules, mode: SearchMode = SearchMode.COMPETITIVE) -> Ruleset:
    modes = dict(LIVE_RULESET.modes)
    modes[mode] = rules
    return dataclasses.replace(LIVE_RULESET, modes=MappingProxyType(modes))


def _with_extra_row(row: TagRelationship) -> Ruleset:
    tags = LIVE_RULESET.tags
    return dataclasses.replace(
        LIVE_RULESET,
        tags=dataclasses.replace(
            tags, relationship_matrix=tags.relationship_matrix + (row,)
        ),
    )


def _with_intent_row(mode: SearchMode, row: dict[str, float]) -> Ruleset:
    alignment = dict(LIVE_RULESET.intent.alignment)
    alignment[mode] = MappingProxyType(row)
    return dataclasses.replace(
        LIVE_RULESET,
        intent=dataclasses.replace(
            LIVE_RULESET.intent, alignment=MappingProxyType(alignment)
        ),
    )


def _with_distance(*, full_marks_within: float, zero_at: float) -> Ruleset:
    return dataclasses.replace(
        LIVE_RULESET,
        distance=dataclasses.replace(
            LIVE_RULESET.distance,
            full_marks_within=full_marks_within,
            zero_at=zero_at,
        ),
    )
