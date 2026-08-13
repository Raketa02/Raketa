"""The rating context's domain events — the two aggregates' streams.

Events carry **primitive** fields (a sport as its ``str`` value, not the enum) so
their wire format is stable regardless of how the Python types are later
refactored. Replaying an assessment's stream reproduces exactly the transcript
the engine consumed; there is no second representation.

Assessment events cover starting, each question being asked (with the selection
reason and the μ and σ that existed at that moment), each answer, and completion.
Rating events cover initialisation today; match, inactivity and status-change
events are reserved for the match-update engine.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class AssessmentStarted:
    assessment_id: UUID
    player_id: UUID
    sport: str
    engine_version: str
    occurred_at: datetime


@dataclass(frozen=True)
class QuestionAsked:
    assessment_id: UUID
    question_id: str
    reason: str
    mu: float
    sigma: float
    occurred_at: datetime


@dataclass(frozen=True)
class AnswerSubmitted:
    assessment_id: UUID
    question_id: str
    option_id: str
    occurred_at: datetime


@dataclass(frozen=True)
class AssessmentCompleted:
    assessment_id: UUID
    mu: float
    sigma: float
    confidence: int
    range_low: float
    range_high: float
    band_name: str
    band_lower: float
    band_upper: float
    status: str
    questions_asked: int
    engine_version: str
    occurred_at: datetime


@dataclass(frozen=True)
class RatingInitialised:
    rating_id: UUID
    player_id: UUID
    sport: str
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
    source_assessment_id: UUID
    occurred_at: datetime
