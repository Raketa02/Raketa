"""The ``AssessmentEngine`` Protocol and the vocabulary it speaks.

A module depends on this abstraction, never on a concrete engine version, so a
version swap — or a future ML-inference implementation behind HTTP — is a wiring
change at the FastAPI boundary like any other port (``docs/adr/0015``).

The engine is *conversational* but *stateless*: it takes the whole accumulated
transcript on every call and holds nothing between them. Given the same
transcript it always returns the same step, which is what lets the rating module
replay an assessment's event stream and reproduce exactly the questions the
engine asked.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from app.kernel import Sport


@dataclass(frozen=True)
class AnswerOption:
    """One selectable answer: an id the engine reads and text the player sees."""

    id: str
    text: str


@dataclass(frozen=True)
class Question:
    """A question as the engine hands it out, in reading order.

    ``category`` is the screen title; ``situation`` is the frame the question is
    asked inside; ``tier`` is the difficulty tier (``basic`` / ``standard`` /
    ``discriminating``) for execution questions and ``None`` otherwise.
    """

    id: str
    category: str
    situation: str
    text: str
    qualifier: str
    options: tuple[AnswerOption, ...]
    tier: str | None = None


@dataclass(frozen=True)
class AnsweredQuestion:
    """One entry of the transcript: which question, answered with which option."""

    question_id: str
    option_id: str


Transcript = tuple[AnsweredQuestion, ...]


@dataclass(frozen=True)
class BandView:
    """A band as it travels on a result: its name and its own boundaries."""

    name: str
    lower: float
    upper: float


# How urgently the rating wants real matches to calibrate it. Raised when the
# assessment ended with answers that still disagreed, because the estimate then
# rests on evidence the questionnaire could not settle.
CALIBRATION_PRIORITY_STANDARD = "standard"
CALIBRATION_PRIORITY_ELEVATED = "elevated"

# Which way one evidence category pulled, relative to where the estimate landed.
# A direction is *computed* — the category fused on its own and compared against
# the final estimate — never authored, so it cannot drift from the arithmetic.
FACTOR_DIRECTION_UP = "up"
FACTOR_DIRECTION_DOWN = "down"
FACTOR_DIRECTION_NEUTRAL = "neutral"


@dataclass(frozen=True)
class ResultFactor:
    """One evidence category's contribution to the estimate, as a row.

    ``key`` is stable and machine-readable; ``label`` is server-authored copy, so
    wording changes without a client release. ``level`` is what this category
    says fused on its own, and ``direction`` is that level compared against the
    final estimate. There is no colour, no glyph and no ordering field — the
    client owns presentation.
    """

    key: str
    label: str
    direction: str
    level: float


@dataclass(frozen=True)
class UncertaintyFactor:
    """Something that widened the range rather than moving the estimate.

    A layoff, an unresolved disagreement, an uneven profile: each reports the σ
    it actually added to the final uncertainty, so a contributor the σ floor
    absorbed entirely is not claimed to have done anything.
    """

    key: str
    label: str
    detail: str
    sigma_added: float


@dataclass(frozen=True)
class ConfidenceReason:
    """Why confidence landed where it did: a stable key and the sentence shown.

    The key is what a projection or a support agent reads; the sentence is
    server-authored copy, so wording changes without a client release. Which
    branch applies is decided by the situation that actually produced it — the
    contributor that widened uncertainty most — and not by an authored ordering.
    """

    key: str
    sentence: str


@dataclass(frozen=True)
class AssessmentResult:
    """The finalised rating: numbers, the band's boundaries, and the explanation.

    Colours, glyphs and ordering are the client's. ``factors`` are the evidence
    categories that moved the estimate; ``uncertainty_factors`` are the ones that
    widened the range instead, kept apart because they are different claims about
    the player.
    """

    mu: float
    sigma: float
    confidence: int
    range_low: float
    range_high: float
    band: BandView
    status: str
    questions_asked: int
    engine_version: str
    calibration_priority: str = CALIBRATION_PRIORITY_STANDARD
    confidence_reason: ConfidenceReason | None = None
    factors: tuple[ResultFactor, ...] = ()
    uncertainty_factors: tuple[UncertaintyFactor, ...] = ()


@dataclass(frozen=True)
class AskQuestion:
    """The engine wants one more answer before it will commit to a result.

    ``reason`` and the ``mu`` / ``sigma`` snapshot are the routing rationale — why
    this question was chosen and the estimate that existed at that moment — so the
    caller can record every routing decision without reaching into the engine.
    """

    question: Question
    reason: str
    mu: float
    sigma: float


@dataclass(frozen=True)
class Complete:
    """The engine has enough evidence; the caller should now ``finalize``.

    ``reason`` and ``value`` are the stop rationale — why the questionnaire ended
    and the number that drove the decision (the marginal gain that fell below
    threshold, the ceiling that was hit) — so a stop is recorded with the value
    that caused it, exactly as every ``AskQuestion`` records why it was asked.
    """

    reason: str
    value: float


Step = AskQuestion | Complete


@runtime_checkable
class AssessmentEngine(Protocol):
    """A pure, versioned assessment engine.

    ``next_step`` decides what to ask next (or that it is done) from the
    transcript so far; ``finalize`` turns a transcript into a rating. Neither
    reads a clock, draws randomness, or mutates the engine.
    """

    @property
    def version(self) -> str: ...

    def next_step(self, *, sport: Sport, transcript: Transcript) -> Step: ...

    def finalize(self, *, sport: Sport, transcript: Transcript) -> AssessmentResult: ...
