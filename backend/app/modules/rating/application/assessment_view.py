"""The current state of an assessment, derived from its replayed stream.

The client holds no flow state, so every read of an assessment answers the same
question the mutation responses do: *what is the current step* — the outstanding
question, the final result, or neither once it has been abandoned. Because the
engine is deterministic, the outstanding question is reproduced from the answered
transcript rather than stored a second time.
"""

from __future__ import annotations

from app.engines.assessment import AskQuestion, AssessmentEngine, Question
from app.modules.rating.application.commands import AssessmentStep
from app.modules.rating.domain.assessment import Assessment


def outstanding_question(engine: AssessmentEngine, assessment: Assessment) -> Question:
    step = engine.next_step(sport=assessment.sport, transcript=assessment.transcript)
    assert isinstance(step, AskQuestion)
    return step.question


def current_step(engine: AssessmentEngine, assessment: Assessment) -> AssessmentStep:
    if assessment.is_completed:
        return AssessmentStep(
            assessment_id=assessment.id,
            status=assessment.status.value,
            question=None,
            result=assessment.result,
        )
    if assessment.is_abandoned:
        return AssessmentStep(
            assessment_id=assessment.id,
            status=assessment.status.value,
            question=None,
            result=None,
        )
    return AssessmentStep(
        assessment_id=assessment.id,
        status=assessment.status.value,
        question=outstanding_question(engine, assessment),
        result=None,
    )
