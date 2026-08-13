"""Wire schemas for the assessment endpoints.

The result payload is numbers plus the band's own boundaries plus a
server-authored status — no colours, no glyphs, no ordering. The client owns
presentation. Factor rows and the confidence-reason sentence arrive with the
explained result (#9).
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.engines.assessment import AssessmentResult, Question
from app.kernel import Sport
from app.modules.rating.application.commands import AssessmentStep


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


class ResultResponse(BaseModel):
    mu: float
    sigma: float
    confidence: int
    range: RangeResponse
    band: BandResponse
    status: str
    questions_asked: int
    engine_version: str

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
        )


class AssessmentStepResponse(BaseModel):
    """The server-driven step. Exactly one of ``question`` / ``result`` is set."""

    assessment_id: str
    status: str
    question: QuestionResponse | None = None
    result: ResultResponse | None = None

    @classmethod
    def from_step(cls, step: AssessmentStep) -> "AssessmentStepResponse":
        return cls(
            assessment_id=str(step.assessment_id),
            status=step.status,
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
