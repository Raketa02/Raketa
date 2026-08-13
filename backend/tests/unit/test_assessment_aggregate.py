"""The Assessment aggregate — replay reproduces the transcript, and the
outstanding-question invariant holds."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.engines.assessment import AnsweredQuestion, AssessmentResult, BandView
from app.kernel import Sport
from app.modules.rating.domain.assessment import Assessment
from app.modules.rating.domain.errors import QuestionNotOutstanding

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
