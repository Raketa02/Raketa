"""Wire schemas for the rating context — assessments and the ratings a player holds.

The result payload is numbers, the band's own boundaries, computed directions and
server-authored copy — no colours, no glyphs, no ordering. The client owns
presentation, and the two clients do not share a shape, so anything decided here
is a decision one of them would have to undo.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.engines.assessment import (
    AssessmentResult,
    ConfidenceReason,
    Question,
    ResultFactor,
    UncertaintyFactor,
)
from app.kernel import Sport
from app.modules.rating.application.commands import AssessmentStep, RatingView


class CreateAssessmentRequest(BaseModel):
    sport: Sport


class SubmitAnswerRequest(BaseModel):
    question_id: str = Field(..., min_length=1)
    option_id: str = Field(..., min_length=1)


class AnswerOptionResponse(BaseModel):
    id: str
    text: str


class QuestionResponse(BaseModel):
    """A question in reading order: category, situation, question, answers."""

    id: str
    category: str
    tier: str | None
    situation: str
    text: str
    qualifier: str
    options: list[AnswerOptionResponse]

    @classmethod
    def from_domain(cls, question: Question) -> "QuestionResponse":
        return cls(
            id=question.id,
            category=question.category,
            tier=question.tier,
            situation=question.situation,
            text=question.text,
            qualifier=question.qualifier,
            options=[
                AnswerOptionResponse(id=option.id, text=option.text)
                for option in question.options
            ],
        )


class RangeResponse(BaseModel):
    low: float
    high: float


class BandResponse(BaseModel):
    name: str
    lower: float
    upper: float


class FactorResponse(BaseModel):
    """One evidence category's row: what it says, and which way it pulled.

    ``direction`` is one of ``up`` / ``down`` / ``neutral``, computed by the
    engine from that category's own evidence against the final estimate. The
    client never derives it — a client-side arrow is a second opinion about the
    arithmetic, and two clients would eventually hold two of them.
    """

    key: str
    label: str
    direction: str
    level: float

    @classmethod
    def from_domain(cls, factor: ResultFactor) -> "FactorResponse":
        return cls(
            key=factor.key,
            label=factor.label,
            direction=factor.direction,
            level=factor.level,
        )


class UncertaintyFactorResponse(BaseModel):
    """Something that widened the range instead of moving the estimate."""

    key: str
    label: str
    detail: str
    sigma_added: float

    @classmethod
    def from_domain(cls, factor: UncertaintyFactor) -> "UncertaintyFactorResponse":
        return cls(
            key=factor.key,
            label=factor.label,
            detail=factor.detail,
            sigma_added=factor.sigma_added,
        )


class ConfidenceReasonResponse(BaseModel):
    """Why confidence landed where it did: a stable key and the sentence shown."""

    key: str
    sentence: str

    @classmethod
    def from_domain(cls, reason: ConfidenceReason) -> "ConfidenceReasonResponse":
        return cls(key=reason.key, sentence=reason.sentence)


class ResultResponse(BaseModel):
    mu: float
    sigma: float
    confidence: int
    range: RangeResponse
    band: BandResponse
    status: str
    questions_asked: int
    engine_version: str
    calibration_priority: str
    confidence_reason: ConfidenceReasonResponse | None = None
    factors: list[FactorResponse] = Field(default_factory=list)
    uncertainty_factors: list[UncertaintyFactorResponse] = Field(default_factory=list)

    @classmethod
    def from_domain(cls, result: AssessmentResult) -> "ResultResponse":
        return cls(
            mu=result.mu,
            sigma=result.sigma,
            confidence=result.confidence,
            range=RangeResponse(low=result.range_low, high=result.range_high),
            band=BandResponse(
                name=result.band.name,
                lower=result.band.lower,
                upper=result.band.upper,
            ),
            status=result.status,
            questions_asked=result.questions_asked,
            engine_version=result.engine_version,
            calibration_priority=result.calibration_priority,
            confidence_reason=(
                ConfidenceReasonResponse.from_domain(result.confidence_reason)
                if result.confidence_reason is not None
                else None
            ),
            factors=[FactorResponse.from_domain(factor) for factor in result.factors],
            uncertainty_factors=[
                UncertaintyFactorResponse.from_domain(factor)
                for factor in result.uncertainty_factors
            ],
        )


class RatingResponse(BaseModel):
    """One sport's Skill rating.

    ``mu`` and ``sigma`` are the Level and the Uncertainty — the same spelling
    ``ResultResponse`` already puts on the wire for the same two numbers, so a
    client never has to learn that the rating it was just shown and the rating it
    later reads back are described in two vocabularies.
    """

    sport: Sport
    mu: float
    sigma: float
    confidence: int
    range: RangeResponse
    band: BandResponse
    status: str
    engine_version: str
    updated_at: datetime

    @classmethod
    def from_view(cls, rating: RatingView) -> "RatingResponse":
        return cls(
            sport=rating.sport,
            mu=rating.mu,
            sigma=rating.sigma,
            confidence=rating.confidence,
            range=RangeResponse(low=rating.range_low, high=rating.range_high),
            band=BandResponse(
                name=rating.band_name,
                lower=rating.band_lower,
                upper=rating.band_upper,
            ),
            status=rating.status,
            engine_version=rating.engine_version,
            updated_at=rating.updated_at,
        )


class RatingsResponse(BaseModel):
    """Every sport this player is rated at — empty when they are rated at none."""

    ratings: list[RatingResponse]

    @classmethod
    def from_views(cls, ratings: list[RatingView]) -> "RatingsResponse":
        return cls(ratings=[RatingResponse.from_view(rating) for rating in ratings])


class AssessmentStepResponse(BaseModel):
    """The server-driven step. Exactly one of ``question`` / ``result`` is set."""

    assessment_id: str
    status: str
    questions_asked: int = Field(
        ...,
        description=(
            "How many of this run's questions have been answered. The outstanding "
            "`question` is **not** counted — it has been put to the player but not "
            "answered — so a question counter reads this plus one, and a fresh run "
            "reports 0. Replayed from the transcript on every read, which is what "
            "lets a resumed run report the position it is really at rather than "
            "restarting at 1. Once the run is over this is the same number "
            "`result.questions_asked` carries."
        ),
    )
    question: QuestionResponse | None = None
    result: ResultResponse | None = None

    @classmethod
    def from_step(cls, step: AssessmentStep) -> "AssessmentStepResponse":
        return cls(
            assessment_id=str(step.assessment_id),
            status=step.status,
            questions_asked=step.questions_asked,
            question=(
                QuestionResponse.from_domain(step.question)
                if step.question is not None
                else None
            ),
            result=(
                ResultResponse.from_domain(step.result)
                if step.result is not None
                else None
            ),
        )
