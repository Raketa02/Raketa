"""The rating context's domain events — the two aggregates' streams.

Events carry **primitive** fields (a sport as its ``str`` value, not the enum) so
their wire format is stable regardless of how the Python types are later
refactored. Replaying an assessment's stream reproduces exactly the transcript
the engine consumed; there is no second representation.

Assessment events cover starting, each question being asked (with the selection
reason and the μ and σ that existed at that moment), each answer, each revision
of an answer, completion, and abandonment — the two terminal states an assessment
stream can reach. Nothing is ever deleted or rewritten: a revision is an
**appended** event and the transcript truncates when it replays one.
Rating events cover initialisation and **one confirmed result moving a Level**;
inactivity is still reserved. There is no separate status-change event: a status
is authored by the rule that moved the rating, so a transition that arrived on its
own would be a second author of a word only one thing decides.

A completion records the **facts** its numbers rest on — including why confidence
landed where it did, and why the questionnaire stopped asking, both as stable
keys. The sentence a key selects is copy and is never stored: freezing copy in
history is how a wording change becomes a migration. The factor rows are likewise
reproduced from the transcript by the engine version that produced them, not
recorded a second time.
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
class AnswerRevised:
    """The player changed an answer they had already given.

    Appended, never applied over the top of the ``AnswerSubmitted`` it replaces:
    the stream is the record of what happened, and *the player changed their
    mind, and to what* is exactly the kind of gap a future model would otherwise
    learn from. The **transcript** is the projection that moves — replaying this
    truncates it at ``question_id`` and puts this option there instead, because
    every answer after it was pitched at a difficulty chosen from the estimate as
    it then stood (``docs/adr/0020``).

    What it deliberately does not carry is what it superseded: the option it
    replaced and the answers it discarded are both in the events already on the
    stream, and recording them here would be the same facts in two places and so
    two places for them to disagree. A projection that wants "what did this
    player change, and from what" replays the prefix, which is the same walk the
    engine's own determinism already rests on.
    """

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
    # Why the questionnaire stopped asking, and the number that drove it — the
    # counterpart to a ``QuestionAsked``'s reason and its μ/σ snapshot. Without
    # them the one routing decision missing from the stream is the last one: an
    # aggregate that records why every question *was* asked, and nothing about
    # the moment it decided to ask no more. Absent means one thing and
    # permanently — *completed before stops were recorded* — never "unknown".
    stop_reason: str | None = None
    stop_value: float | None = None


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


@dataclass(frozen=True)
class RatingMovedOnResult:
    """One confirmed counted result, applied. **The only thing that tests a rating.**

    ``game_id`` is what makes the catch-up idempotent and is the reason there is
    no cursor anywhere: replaying this stream answers *have I applied that game*,
    so a run that dies half way costs a repeat of the read and never a repeat of
    the move (``docs/adr/0139``).

    ``occurred_at`` is **when the result became final**, not when the catch-up
    noticed it. A confirmation is a clock passing, and dating this event from the
    run that spotted it would make the same history produce different streams on
    a laptop that was switched off for a week.

    **Both deltas are recorded and only one of them happened.** The pair is what
    the card promised before the game and what the rule computed after it, and
    they are the same object by construction — so a support question of the shape
    *why did my Level move by that* is answered off the stream rather than by
    re-deriving arithmetic against ratings that have since moved.

    The opposing side is recorded as **the one player it was priced against**: a
    four's two opponents are averaged into one Level and one uncertainty before
    anything is computed, and storing the pair separately would be storing the
    inputs to a mean nobody would recompute.
    """

    rating_id: UUID
    player_id: UUID
    sport: str
    game_id: UUID
    won: bool
    opposition_mu: float
    opposition_sigma: float
    information_share: float
    win_delta: float
    loss_delta: float
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
    occurred_at: datetime
