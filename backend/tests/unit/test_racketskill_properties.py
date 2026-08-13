"""Bounds that must hold for *every* answer pattern, not just the six personas.

These are the opposite of the persona file: nothing here should move when a
constant is retuned. A retune that breaks one of these has broken the model, not
the baseline.

The sweep is a seeded pseudo-random walk rather than a property-based library, so
it adds no dependency and a failure is reproducible from the seed printed in the
assertion. It covers all four sports, since the question bank is per sport.
"""

import random

from app.engines.assessment import AnsweredQuestion, AskQuestion, Complete
from app.engines.racketskill.core import (
    SCALE_MAX,
    SCALE_MIN,
    Band,
    band_for,
)
from app.engines.racketskill.v3 import RacketSkillEngineV3
from app.engines.racketskill.v3.engine import (
    CONFIDENCE_CAP,
    MAX_QUESTIONS,
    SIGMA_FLOOR,
)
from app.kernel import Sport

CONFIDENCE_CEILING = round(CONFIDENCE_CAP * 100)
WALKS_PER_SPORT = 60


def _walk(sport: Sport, seed: int):
    """One assessment answered by a seeded random policy."""

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
    return engine.finalize(sport=sport, transcript=transcript)


def test_every_answer_pattern_stays_inside_its_bounds() -> None:
    for sport in Sport:
        for seed in range(WALKS_PER_SPORT):
            result = _walk(sport, seed)
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
