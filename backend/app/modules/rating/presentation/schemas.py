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
from app.modules.rating.application.commands import (
    AssessmentStep,
    InProgressAssessmentView,
    TranscriptEntry,
)
from app.modules.rating.domain.skill_rating import SkillRating


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


class TranscriptEntryResponse(BaseModel):
    """One answered question: the question as it was asked, and what was chosen."""

    # ``option_id`` names one of ``question.options``, whose text is right there —
    # carrying the text again would be one string in two places and so one string
    # that can disagree with itself.
    #
    # Kept as a comment rather than added to the docstring above, because a
    # response model's docstring *is* wire copy: it lands in the API document as
    # the schema description, so a note to the next reader there is a contract
    # diff. The one line that remains is written to be read by a client.
    question: QuestionResponse
    option_id: str

    @classmethod
    def from_domain(cls, entry: TranscriptEntry) -> "TranscriptEntryResponse":
        return cls(
            question=QuestionResponse.from_domain(entry.question),
            option_id=entry.option_id,
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
    # The ceiling is a fact about the rating — the most this questionnaire could
    # ever have proved about anybody — and not a drawing instruction. A client
    # marking it on a ring is presentation the client owns; *what the number is*
    # was never the client's to know, and it held a copy until this field existed.
    mu: float
    sigma: float
    confidence: int
    confidence_ceiling: int | None = Field(
        None,
        description=(
            "The highest `confidence` this engine version can reach, as a whole "
            "percent — a questionnaire has an irreducible limit, so a rating at "
            "this value was held by the ceiling and one below it by its own "
            "evidence. Absent only for a rating replayed from an engine version "
            "that has since been retired, which is the same case that carries no "
            "`confidence_reason`: such a rating keeps its numbers and loses its "
            "explanation. Do not hold a local copy of this number — it is "
            "version-scoped and may be retuned without a client release."
        ),
    )
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
            confidence_ceiling=result.confidence_ceiling,
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

    # Built from the aggregate, exactly as ``ResultResponse`` is built from the
    # engine's result: one policy for how the six rating facts reach the wire.
    # Kept as a comment rather than added to the docstring above, because a
    # response model's docstring *is* wire copy — it lands in both API documents
    # as the schema description, so a note to the next reader here would have
    # been a contract diff.
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
    def from_domain(cls, rating: SkillRating) -> "RatingResponse":
        # The band travels as the engine computed it. Its boundaries are
        # deliberately uneven and were wrong once already, so nothing downstream
        # may restate them.
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
    def from_domain(cls, ratings: list[SkillRating]) -> "RatingsResponse":
        return cls(ratings=[RatingResponse.from_domain(rating) for rating in ratings])


class AssessmentStepResponse(BaseModel):
    """The server-driven step: at most one of `question` / `result` is set, and
    `transcript` is everything already answered behind it. Neither means the run
    is not asking and has not been rated — see `status`."""

    # The invariant was *exactly* one until the questionnaire's stop and the
    # assessment's completion became two moments (docs/adr/0020). Both absent is
    # now a state a live run passes through and sits in, and `status` is what
    # separates it from an abandoned run. Weakening it rather than adding a flag
    # keeps every field where it was: no client that reads `question` first has
    # to learn a new one.
    #
    # Kept as a comment rather than added to the docstring above, because a
    # response model's docstring *is* wire copy: it lands in the API document as
    # the schema description. The lines that remain are written for a client.
    assessment_id: str
    status: str = Field(
        ...,
        description=(
            "`in_progress`, `completed` or `abandoned` — and the field that says "
            "which of two things *neither a question nor a result* means.\n\n"
            "- `in_progress` **with** a `question`: the questionnaire, awaiting "
            "that answer.\n"
            "- `in_progress` with **neither**: the questionnaire has **stopped**. "
            "No remaining question would meaningfully tighten the estimate, and "
            "nothing has been rated — every answer is still revisable, and "
            "`POST /assessments/{assessment_id}/completion` is what creates the "
            "Skill rating.\n"
            "- `completed`: the `result` is here and the answers are settled.\n"
            "- `abandoned`: neither, and the run ended without a rating."
        ),
    )
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
    transcript: list[TranscriptEntryResponse] = Field(
        ...,
        description=(
            "Every answer given in this run so far, in the order they were given, "
            "each with the question it answered **as that question was asked** — "
            "so an answered question can be rendered from the response alone, by a "
            "client that was never shown it. Empty, never absent, on a run with no "
            "answers yet: a fresh run and a run whose answers are being withheld "
            "are not two readings of one payload. Grows by one entry per answer "
            "and is replayed from the stream on every read, so it survives a "
            "reinstall and a second device with nothing cached locally. Length is "
            "`questions_asked`; the outstanding `question` is not in it, because it "
            "has not been answered."
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
            transcript=[
                TranscriptEntryResponse.from_domain(entry) for entry in step.transcript
            ],
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


class InProgressAssessmentResponse(BaseModel):
    """One unfinished run: which assessment, and which sport it is for.

    Carries no question, no result and no progress. A caller reading this is
    deciding *where to send the player*; it re-reads the run it routes to, and
    that read is the one that reproduces the outstanding question.
    """

    assessment_id: str
    sport: Sport

    @classmethod
    def from_view(
        cls, entry: InProgressAssessmentView
    ) -> "InProgressAssessmentResponse":
        return cls(assessment_id=str(entry.assessment_id), sport=entry.sport)


class InProgressAssessmentsResponse(BaseModel):
    """Every unfinished run this player holds — empty when they hold none.

    Empty is the ordinary answer for a new account and for a player who has
    finished everything they started, so it is a 200 with an empty list rather
    than a 404 or the singular form's 204.

    Ordered by the sport registry, so a caller that wants one run can take the
    first entry.
    """

    assessments: list[InProgressAssessmentResponse]

    @classmethod
    def from_views(
        cls, entries: list[InProgressAssessmentView]
    ) -> "InProgressAssessmentsResponse":
        return cls(
            assessments=[
                InProgressAssessmentResponse.from_view(entry) for entry in entries
            ]
        )
