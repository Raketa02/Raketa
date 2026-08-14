"""The Assessment aggregate — replay reproduces the transcript, and the
outstanding-question invariant holds."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.engines.assessment import (
    CALIBRATION_PRIORITY_STANDARD,
    AnsweredQuestion,
    AssessmentResult,
    BandView,
)
from app.engines.racketskill.v3 import RacketSkillEngineV3
from app.kernel import Sport
from app.modules.rating.application.assessment_view import completed_result
from app.modules.rating.domain.assessment import Assessment
from app.modules.rating.domain.errors import (
    AssessmentAlreadyFinished,
    QuestionNotOutstanding,
)

NOW = datetime(2026, 8, 13, tzinfo=timezone.utc)


def _result() -> AssessmentResult:
    return AssessmentResult(
        mu=1.40,
        sigma=0.9821,
        confidence=18,
        range_low=1.0,
        range_high=2.38,
        band=BandView(name="New", lower=1.0, upper=2.0),
        status="Initial Estimate",
        questions_asked=1,
        engine_version="racketskill-fusion-v3",
    )


def _started() -> Assessment:
    assessment = Assessment.start(
        assessment_id=uuid4(),
        player_id=uuid4(),
        sport=Sport.PADEL,
        engine_version="racketskill-fusion-v3",
        occurred_at=NOW,
    )
    assessment.ask(
        question_id="opening.regularity",
        reason="opening",
        mu=2.6,
        sigma=2.6,
        occurred_at=NOW,
    )
    return assessment


def test_replay_reproduces_transcript_and_result() -> None:
    assessment = _started()
    assessment.answer(
        question_id="opening.regularity", option_id="never-played", occurred_at=NOW
    )
    assessment.complete(result=_result(), occurred_at=NOW)

    replayed = Assessment.from_history(assessment.pull_events())

    assert replayed.transcript == (
        AnsweredQuestion("opening.regularity", "never-played"),
    )
    assert replayed.is_completed
    assert replayed.result == _result()
    assert replayed.version == assessment.version


def test_answer_is_rejected_when_not_outstanding() -> None:
    assessment = _started()
    with pytest.raises(QuestionNotOutstanding):
        assessment.answer(
            question_id="some.other.question", option_id="x", occurred_at=NOW
        )


def test_a_completed_assessment_rejects_further_answers() -> None:
    assessment = _started()
    assessment.answer(
        question_id="opening.regularity", option_id="never-played", occurred_at=NOW
    )
    assessment.complete(result=_result(), occurred_at=NOW)
    with pytest.raises(QuestionNotOutstanding):
        assessment.answer(
            question_id="opening.regularity",
            option_id="never-played",
            occurred_at=NOW,
        )


def test_abandonment_ends_the_stream_and_survives_replay() -> None:
    assessment = _started()
    assessment.abandon(occurred_at=NOW)

    replayed = Assessment.from_history(assessment.pull_events())

    assert replayed.is_abandoned
    assert not replayed.is_in_progress
    assert replayed.outstanding_question_id is None


def test_an_abandoned_assessment_rejects_further_answers() -> None:
    assessment = _started()
    assessment.abandon(occurred_at=NOW)
    with pytest.raises(QuestionNotOutstanding):
        assessment.answer(
            question_id="opening.regularity",
            option_id="never-played",
            occurred_at=NOW,
        )


def test_abandoning_twice_is_a_no_op() -> None:
    assessment = _started()
    assessment.abandon(occurred_at=NOW)
    assessment.pull_events()

    assessment.abandon(occurred_at=NOW)

    assert assessment.pull_events() == []


def test_a_completed_assessment_cannot_be_abandoned() -> None:
    assessment = _started()
    assessment.answer(
        question_id="opening.regularity", option_id="never-played", occurred_at=NOW
    )
    assessment.complete(result=_result(), occurred_at=NOW)
    with pytest.raises(AssessmentAlreadyFinished):
        assessment.abandon(occurred_at=NOW)


# --- The recorded result, and the explanation reproduced from the transcript ----


def _completed_from(engine, transcript: tuple[AnsweredQuestion, ...]) -> Assessment:
    """An assessment driven to completion by the engine, as the use case does."""

    assessment = Assessment.start(
        assessment_id=uuid4(),
        player_id=uuid4(),
        sport=Sport.PADEL,
        engine_version=engine.version,
        occurred_at=NOW,
    )
    for entry in transcript:
        assessment.ask(
            question_id=entry.question_id,
            reason="test",
            mu=2.6,
            sigma=2.6,
            occurred_at=NOW,
        )
        assessment.answer(
            question_id=entry.question_id, option_id=entry.option_id, occurred_at=NOW
        )
    assessment.complete(
        result=engine.finalize(sport=Sport.PADEL, transcript=assessment.transcript),
        occurred_at=NOW,
    )
    return Assessment.from_history(assessment.pull_events())


def test_the_stream_records_the_facts_and_not_the_copy() -> None:
    # A completion records why confidence landed where it did, as a key. The
    # sentence that key selects is copy: it is reproduced, never stored, so
    # rewording it is not a migration.
    engine = RacketSkillEngineV3()
    replayed = _completed_from(
        engine, (AnsweredQuestion("opening.regularity", "never-played"),)
    )
    recorded = replayed.result
    assert recorded is not None
    assert recorded.calibration_priority == CALIBRATION_PRIORITY_STANDARD
    assert recorded.confidence_reason is None  # copy is not replayed
    assert recorded.factors == ()


def test_the_reproduced_explanation_agrees_with_the_recorded_numbers() -> None:
    # The explanation is derived rather than stored, so this is the guarantee
    # that makes that safe: the numbers a client is served are, to the digit, the
    # numbers on the stream. A card can never print a band that disagrees with
    # the level beside it, because there is only ever one computation.
    engine = RacketSkillEngineV3()
    transcript = (
        AnsweredQuestion("opening.regularity", "frequent"),
        AnsweredQuestion("context.environment", "env3"),
        AnsweredQuestion("context.relative", "r3"),
        AnsweredQuestion("execution.basic", "e0"),
        AnsweredQuestion("execution.standard", "e0"),
    )
    replayed = _completed_from(engine, transcript)
    recorded = replayed.result
    served = completed_result(engine, replayed)
    assert recorded is not None and served is not None

    assert (served.mu, served.sigma, served.confidence) == (
        recorded.mu,
        recorded.sigma,
        recorded.confidence,
    )
    assert served.band == recorded.band
    assert (served.range_low, served.range_high) == (
        recorded.range_low,
        recorded.range_high,
    )
    assert served.calibration_priority == recorded.calibration_priority
    # And the explanation the recorded result cannot carry is there.
    assert served.factors and served.confidence_reason is not None


def test_a_result_from_a_retired_engine_keeps_its_number_and_loses_its_commentary() -> (
    None
):
    # A later version would explain the transcript its own way, which is not what
    # the player was shown. The recorded result stands, unexplained, rather than
    # acquiring commentary that was never true of it.
    engine = RacketSkillEngineV3()
    replayed = _completed_from(
        engine, (AnsweredQuestion("opening.regularity", "never-played"),)
    )
    replayed.engine_version = "racketskill-fusion-v4"

    served = completed_result(engine, replayed)
    assert served == replayed.result
    assert served is not None and served.factors == ()
