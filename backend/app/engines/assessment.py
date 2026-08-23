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


# The Rating status a questionnaire alone can produce, and the only one any live
# engine emits: the glossary's **Initial Estimate**, before a counted match has
# moved anything. It lives here rather than inside an engine version because it
# is *read* outside the engines — Now's *New on Raketa* shelf prints a quiet
# marker exactly when a Level rests on nothing but answers (ADR-0051) — and a
# reader holding its own copy of the string is comparing against a value nothing
# keeps honest, which is the argument `confidence_ceiling` below already makes
# for travelling with the result.
STATUS_INITIAL_ESTIMATE = "Initial Estimate"

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
    #: The highest Confidence this engine version can reach, as a whole percent —
    #: its σ floor put through its own confidence transform. It travels with the
    #: rating rather than being known separately, because a reader comparing a
    #: Confidence against a ceiling it holds its own copy of is comparing against
    #: a number nothing keeps honest: retune the floor and the two disagree
    #: silently, in the direction of telling a player their answers were the
    #: limit when the questionnaire was.
    #:
    #: Absent under exactly the rule ``confidence_reason`` is absent: a result
    #: replayed from its stream because the engine that produced it has been
    #: retired keeps its numbers and loses its explanation, and what a *retired*
    #: engine could prove is part of that explanation. Every live result carries
    #: it.
    confidence_ceiling: int | None = None
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

    **The finalised result is deliberately not carried here, and this note is so
    that is not re-proposed.** Folding it in looks like it would save the caller
    a ``finalize`` call, and it would: there is one implementation and one
    non-test caller. But ``next_step`` is the routing half of the engine, asked
    on every answer by a caller that only wants to know whether there is another
    question. Returning a result would make every terminating call author the
    player-facing copy ``finalize`` owns — the confidence sentence, the factor
    labels, the widener detail — for a caller that may not want it. Callers that
    do want it ask for it, which is also what keeps a completed run's result
    reproducible from its transcript rather than from a step nobody kept.
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
