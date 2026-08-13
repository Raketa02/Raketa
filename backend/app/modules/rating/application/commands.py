"""Commands and the step view the rating use cases speak in."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.engines.assessment import AssessmentResult, Question
from app.kernel import Sport


@dataclass(frozen=True)
class CreateAssessmentCommand:
    player_id: UUID
    sport: Sport


@dataclass(frozen=True)
class SubmitAnswerCommand:
    player_id: UUID
    assessment_id: UUID
    question_id: str
    option_id: str


@dataclass(frozen=True)
class AssessmentStep:
    """The server-driven step: the current question, or the final result.

    Exactly one of ``question`` / ``result`` is set. The client holds no flow
    state — this mutation response *is* the current state of the assessment.
    """

    assessment_id: UUID
    status: str
    question: Question | None
    result: AssessmentResult | None
