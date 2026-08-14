"""RacketSkill engine, exercised only through its Protocol methods.

The internal fusion, encoding and banding functions are deliberately not tested
directly — the interesting behaviours are emergent. The beginner persona is a
golden test, *designed* to break on a constant retune and force a deliberate
re-baseline.
"""

from app.engines.assessment import AnsweredQuestion, AskQuestion, Complete
from app.engines.racketskill.core import (
    SCALE_MAX,
    SCALE_MIN,
    Band,
    band_for,
    confidence_percent,
)
from app.engines.racketskill.v3 import RacketSkillEngineV3
from app.engines.racketskill.v3.questions import (
    NEVER_PLAYED_OPTION_ID,
    OPENING_QUESTION_ID,
)
from app.kernel import Sport

BEGINNER = (AnsweredQuestion(OPENING_QUESTION_ID, NEVER_PLAYED_OPTION_ID),)


def test_opening_question_shape() -> None:
    engine = RacketSkillEngineV3()
    step = engine.next_step(sport=Sport.PADEL, transcript=())
    assert isinstance(step, AskQuestion)
    question = step.question
    assert question.id == OPENING_QUESTION_ID
    assert question.category and question.situation and question.text
    assert question.qualifier
    assert question.tier is None  # the opening regularity question is not tiered
    assert len(question.options) == 5
    assert len({option.id for option in question.options}) == 5


def test_beginner_answer_finishes_rather_than_asking() -> None:
    engine = RacketSkillEngineV3()
    step = engine.next_step(sport=Sport.TENNIS, transcript=BEGINNER)
    assert isinstance(step, Complete)


def test_beginner_persona_is_exact() -> None:
    engine = RacketSkillEngineV3()
    result = engine.finalize(sport=Sport.PADEL, transcript=BEGINNER)
    assert result.mu == 1.40
    assert result.sigma == 0.9821
    assert result.confidence == 18
    assert (result.range_low, result.range_high) == (1.00, 2.38)
    assert result.band.name == "New"
    assert (result.band.lower, result.band.upper) == (1.0, 1.5)
    assert result.status == "Initial Estimate"
    assert result.questions_asked == 1
    assert result.engine_version == "racketskill-fusion-v3"


def test_engine_is_pure_and_deterministic() -> None:
    engine = RacketSkillEngineV3()
    first = engine.finalize(sport=Sport.PADEL, transcript=BEGINNER)
    second = engine.finalize(sport=Sport.PADEL, transcript=BEGINNER)
    assert first == second
    # The beginner anchor carries no sport-specific evidence.
    assert engine.finalize(sport=Sport.SQUASH, transcript=BEGINNER) == first


def test_confidence_transform_never_reaches_100() -> None:
    # Across the whole scale of σ, including the degenerate σ = 0.
    for hundredths in range(0, 401):
        assert confidence_percent(hundredths / 100.0) <= 99
    assert confidence_percent(0.0) == 99


def test_every_opening_answer_stays_in_bounds_and_below_the_ceiling() -> None:
    engine = RacketSkillEngineV3()
    options = engine.next_step(sport=Sport.PADEL, transcript=()).question.options  # type: ignore[union-attr]
    for option in options:
        result = engine.finalize(
            sport=Sport.PADEL,
            transcript=(AnsweredQuestion(OPENING_QUESTION_ID, option.id),),
        )
        assert SCALE_MIN <= result.mu <= SCALE_MAX
        assert result.sigma >= 0.84  # the σ floor
        assert result.confidence <= 30  # nobody leaves onboarding above 30%


def test_bands_are_ordered_and_all_reachable() -> None:
    assert band_for(1.4) is Band.NEW
    assert band_for(2.5) is Band.DEVELOPING
    assert band_for(3.5) is Band.ESTABLISHED
    assert band_for(4.5) is Band.ADVANCED
    assert band_for(SCALE_MAX) is Band.ADVANCED
    labels = [band_for(mu).label for mu in (1.5, 2.5, 3.5, 4.5)]
    assert labels == ["New", "Developing", "Established", "Advanced"]
