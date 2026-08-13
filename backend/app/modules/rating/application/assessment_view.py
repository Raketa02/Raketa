"""The current state of an assessment, derived from its replayed stream.

The client holds no flow state, so every read of an assessment answers the same
question the mutation responses do: *what is the current step* — the outstanding
question, the final result, or neither once it has been abandoned. Because the
engine is deterministic, the outstanding question is reproduced from the answered
transcript rather than stored a second time.

The finished result is reproduced the same way, and for the same reason. Its
numbers are recorded on the stream, but its *explanation* — the factor rows and
the confidence sentence — is copy and computed direction, and storing those would
freeze wording into history and open the door to a card whose rows disagree with
the number above them.
"""

from __future__ import annotations

from app.engines.assessment import (
    AskQuestion,
    AssessmentEngine,
    AssessmentResult,
    Question,
)
from app.modules.rating.application.commands import AssessmentStep
from app.modules.rating.domain.assessment import Assessment


def outstanding_question(engine: AssessmentEngine, assessment: Assessment) -> Question:
    step = engine.next_step(sport=assessment.sport, transcript=assessment.transcript)
    assert isinstance(step, AskQuestion)
    return step.question


def completed_result(
    engine: AssessmentEngine, assessment: Assessment
) -> AssessmentResult | None:
    """The explained result of a finished assessment.

    Reproducing it is exact only while the engine that produced it is the engine
    asked: a later version would explain the transcript its own way, which is not
    what the player was shown. So the recorded result stands whenever the
    versions differ, and the explanation is simply absent — a rating from a
    retired engine keeps its number and loses its commentary, rather than
    acquiring commentary that was never true of it.
    """

    recorded = assessment.result
    if recorded is None or assessment.engine_version != engine.version:
        return recorded
    return engine.finalize(sport=assessment.sport, transcript=assessment.transcript)


def current_step(engine: AssessmentEngine, assessment: Assessment) -> AssessmentStep:
    if assessment.is_completed:
        return AssessmentStep(
            assessment_id=assessment.id,
            status=assessment.status.value,
            question=None,
            result=completed_result(engine, assessment),
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
