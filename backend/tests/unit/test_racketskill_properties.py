"""Bounds that must hold for *every* answer pattern, not just the six personas.

These are the opposite of the persona file: nothing here should move when a
constant is retuned. A retune that breaks one of these has broken the model, not
the baseline.

The sweep is a seeded pseudo-random walk rather than a property-based library, so
it adds no dependency and a failure is reproducible from the seed printed in the
assertion. It covers all four sports, since the question bank is per sport.
"""

import random

import pytest

from app.engines.assessment import AnsweredQuestion, AskQuestion, Complete
from app.engines.racketskill.core import (
    BAND_EDGE_TOLERANCE,
    SCALE_MAX,
    SCALE_MIN,
    Band,
    band_for,
)
from app.engines.racketskill.v3 import RacketSkillEngineV3
from app.engines.racketskill.v3.engine import (
    CONFIDENCE_CAP,
    ESTABLISHED_FLOOR,
    MAX_QUESTIONS,
    SIGMA_FLOOR,
    TIER_BASIC_BELOW,
    TIER_STANDARD_BELOW,
    _asked_execution_tiers,
    _contradiction,
    _evidence_points,
    _target_tier,
)
from app.engines.racketskill.v3.questions import (
    TIER_BASIC,
    TIER_DISCRIMINATING,
    TIER_STANDARD,
)
from app.kernel import Sport

CONFIDENCE_CEILING = round(CONFIDENCE_CAP * 100)
WALKS_PER_SPORT = 60

#: The contradiction sweep gets its own, larger count. A random walk reaches a
#: disagreement often enough at 60, but almost always by the third-demonstration
#: route — at 60 it produces *no* tie-breaker at all, so a sweep that size would
#: guard one half of the invariant and look like it guarded both. Measured while
#: landing #15: 60 walks/sport → 28 disagreements, 0 tie-breakers; 200 → 104 and 4.
CONTRADICTION_WALKS_PER_SPORT = 200


def _walk(sport: Sport, seed: int):
    """One assessment answered by a seeded random policy, with its transcript."""

    rng = random.Random(seed)
    engine = RacketSkillEngineV3()
    transcript: tuple[AnsweredQuestion, ...] = ()
    while True:
        step = engine.next_step(sport=sport, transcript=transcript)
        if isinstance(step, Complete):
            break
        assert isinstance(step, AskQuestion)
        question = step.question
        option = rng.choice(question.options)
        transcript += (AnsweredQuestion(question.id, option.id),)
    return engine.finalize(sport=sport, transcript=transcript), transcript


def test_every_answer_pattern_stays_inside_its_bounds() -> None:
    for sport in Sport:
        for seed in range(WALKS_PER_SPORT):
            result, _ = _walk(sport, seed)
            where = f"{sport.value} seed={seed}"

            assert SCALE_MIN <= result.mu <= SCALE_MAX, f"level off scale: {where}"
            assert result.sigma >= SIGMA_FLOOR, f"σ below its floor: {where}"

            # Never 100: the engine cannot claim total certainty about anybody,
            # and never above the ceiling: self-report has an irreducible limit.
            assert 0 <= result.confidence <= 99, f"confidence out of range: {where}"
            assert result.confidence <= CONFIDENCE_CEILING, f"ceiling breached: {where}"

            asked = result.questions_asked
            assert asked <= MAX_QUESTIONS, f"too many questions: {where}"
            assert asked >= 1, f"no question asked: {where}"

            # The band travels on the result, so it must agree with the number
            # beside it — this is the bug class that made the boundaries wrong.
            expected = band_for(result.mu)
            assert result.band.name == expected.label, f"band vs level: {where}"
            assert (result.band.lower, result.band.upper) == (
                expected.lower,
                expected.upper,
            ), f"band boundaries not the model's: {where}"

            assert SCALE_MIN <= result.range_low <= result.mu, f"range low: {where}"
            assert result.mu <= result.range_high <= SCALE_MAX, f"range high: {where}"

            assert result.status == "Initial Estimate", f"status: {where}"
            assert result.engine_version, f"no engine version recorded: {where}"


def test_a_disagreement_is_always_tested_at_the_tier_the_claims_imply() -> None:
    """No player's claims are doubted without being put to the test (issue #15).

    This is the guarantee, and the tie-breaker is only one of the two ways the
    engine keeps it. The other is the third demonstration: with three tiers in the
    bank, a player who earns three has necessarily been asked the claims' own
    tier, so no extra question is owed. Which route a player takes turns on
    whether their demonstrations keep the estimate above ``ESTABLISHED_FLOOR``.

    Stated as the invariant rather than as "a contradiction earns a tie-breaker",
    because the latter is false and was the thing that had to be settled here:
    correcting the floor moved most contradicting players onto the demonstration
    route. Verified exhaustively over 512.000 routed padel transcripts while
    landing #15 — every one of the 102.718 that ended in an unresolved
    disagreement had been tested at its claims' tier, none untested — and held
    here across all four sports so a retune cannot quietly break it.

    Both routes have to be *covered* for this to guard the whole invariant, which
    is what ``CONTRADICTION_WALKS_PER_SPORT`` is for. Mutation-checked: deleting
    the tie-breaker turns this red. Re-pinning the floor does *not*, and should
    not — the invariant held under the old constant too, by the tie-breaker doing
    more of the work. It is the routing that moved, not the guarantee.
    """

    seen = 0
    for sport in Sport:
        for seed in range(CONTRADICTION_WALKS_PER_SPORT):
            _, transcript = _walk(sport, seed)
            sides = _contradiction(_evidence_points(transcript))
            if sides is None:
                continue  # no disagreement, nothing owed
            seen += 1
            where = f"{sport.value} seed={seed}"
            assert _target_tier(sides.claims.mu) in _asked_execution_tiers(
                transcript
            ), f"claims doubted but never tested at their own tier: {where}"

    # A sweep that stopped producing disagreements would pass this test without
    # asserting anything, which is the failure mode a bounds sweep hides best.
    assert seen >= 50, f"the sweep found only {seen} disagreements to check"


def test_bands_are_ordered_contiguous_and_cover_the_scale() -> None:
    bands = list(Band)
    assert [b.label for b in bands] == ["New", "Developing", "Established", "Advanced"]
    assert bands[0].lower == SCALE_MIN
    assert bands[-1].upper == SCALE_MAX
    for lower_band, higher_band in zip(bands[:-1], bands[1:], strict=True):
        assert lower_band.upper < higher_band.lower, "bands must not overlap"


def test_band_edges_are_the_specifications_and_not_round_numbers() -> None:
    """Guards the defect issue #10 found: evenly-spaced bands look plausible.

    The widths are deliberately uneven — New and Developing are narrow, so two
    demonstrations separate them, while Established and Advanced each span close
    to a full level, which is what earns a third demonstration.
    """

    assert (Band.NEW.lower, Band.NEW.upper) == (1.0, 1.5)
    assert (Band.DEVELOPING.lower, Band.DEVELOPING.upper) == (1.6, 2.6)
    assert (Band.ESTABLISHED.lower, Band.ESTABLISHED.upper) == (2.7, 3.8)
    assert (Band.ADVANCED.lower, Band.ADVANCED.upper) == (3.9, 5.0)

    # The effective edges sit half the gap below each printed lower bound.
    assert band_for(1.54) is Band.NEW
    assert band_for(1.55) is Band.DEVELOPING
    assert band_for(2.64) is Band.DEVELOPING
    assert band_for(2.65) is Band.ESTABLISHED
    assert band_for(3.84) is Band.ESTABLISHED
    assert band_for(3.85) is Band.ADVANCED


def test_tier_thresholds_are_the_specifications_and_not_round_numbers() -> None:
    """The same defect class as the band edges, in the router (issue #15).

    These were rounded to 2,5 and 3,5, which asked a slice of every band's lower
    half at the tier below the one it had earned — and an answer is worth what its
    tier says it is worth, so the rounding changed what players' answers meant.

    Asserted on either side of each edge rather than by reading the constant, so
    the *boundary* is what is pinned and not merely the literal's spelling.
    """

    assert (TIER_BASIC_BELOW, TIER_STANDARD_BELOW) == (2.45, 3.15)

    assert _target_tier(2.44) == TIER_BASIC
    assert _target_tier(2.45) == TIER_STANDARD
    assert _target_tier(3.14) == TIER_STANDARD
    assert _target_tier(3.15) == TIER_DISCRIMINATING

    # Each threshold sits just under the band edge above it, as `band_for` sees
    # that edge: the harder vocabulary arrives while the player is still climbing
    # towards the band that owns it, not once they have already arrived.
    assert TIER_BASIC_BELOW < Band.ESTABLISHED.lower - BAND_EDGE_TOLERANCE
    assert TIER_STANDARD_BELOW < Band.ADVANCED.lower - BAND_EDGE_TOLERANCE


def test_the_router_and_the_band_agree_on_reaching_established() -> None:
    """"Has climbed into Established" must mean one thing, not two (issue #15).

    ``ESTABLISHED_FLOOR`` decides who earns a third demonstration and ``band_for``
    decides what the result is called. A literal in the router is how the two
    drifted apart once already: the bands moved to their specified uneven edges
    and the floor stayed where the even ones had put it, so a player could be
    called Established by the result and Developing by the routing.
    """

    assert ESTABLISHED_FLOOR == Band.ESTABLISHED.lower - BAND_EDGE_TOLERANCE
    assert ESTABLISHED_FLOOR == pytest.approx(2.65)

    # The property that matters: the floor is exactly where the band starts.
    assert band_for(ESTABLISHED_FLOOR) is Band.ESTABLISHED
    assert band_for(ESTABLISHED_FLOOR - 0.01) is Band.DEVELOPING
