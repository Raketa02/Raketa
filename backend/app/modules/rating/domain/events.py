"""The rating context's domain events — the two aggregates' streams.

Events carry **primitive** fields (a sport as its ``str`` value, not the enum) so
their wire format is stable regardless of how the Python types are later
refactored. Replaying an assessment's stream reproduces exactly the transcript
the engine consumed; there is no second representation.

Assessment events cover starting, each question being asked (with the selection
reason and the μ and σ that existed at that moment), each answer, completion, and
abandonment — the two terminal states an assessment stream can reach.
Rating events cover initialisation today; match, inactivity and status-change
events are reserved for the match-update engine.

A completion records the **facts** its numbers rest on — including why confidence
landed where it did, as a stable key. The sentence that key selects is copy and is
never stored: freezing copy in history is how a wording change becomes a
migration. The factor rows are likewise reproduced from the transcript by the
engine version that produced them, not recorded a second time.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.engines.assessment import CALIBRATION_PRIORITY_STANDARD


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
    # Appended after ``occurred_at`` because they carry defaults: a stream
    # written before they existed decodes with them, and adds no migration.
    calibration_priority: str = CALIBRATION_PRIORITY_STANDARD
    confidence_reason_key: str | None = None


@dataclass(frozen=True)
class AssessmentAbandoned:
    assessment_id: UUID
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
    calibration_priority: str = CALIBRATION_PRIORITY_STANDARD
    confidence_reason_key: str | None = None
