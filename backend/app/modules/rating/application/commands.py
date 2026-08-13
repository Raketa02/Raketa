"""Commands and the step view the rating use cases speak in."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
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
class GetAssessmentQuery:
    player_id: UUID
    assessment_id: UUID


@dataclass(frozen=True)
class FindInProgressQuery:
    player_id: UUID
    sport: Sport


@dataclass(frozen=True)
class AbandonAssessmentCommand:
    player_id: UUID
    assessment_id: UUID


@dataclass(frozen=True)
class ListRatingsQuery:
    player_id: UUID


@dataclass(frozen=True)
class RatingView:
    """One sport's Skill rating as a reader sees it.

    A view rather than the aggregate itself: the aggregate carries its event
    recorder and its stream version, neither of which is a fact about the rating,
    and a read path that hands those to presentation invites a write through a
    read.
    """

    sport: Sport
    mu: float
    sigma: float
    confidence: int
    range_low: float
    range_high: float
    band_name: str
    band_lower: float
    band_upper: float
    status: str
    engine_version: str
    updated_at: datetime


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
