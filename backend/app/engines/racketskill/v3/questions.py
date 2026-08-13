"""Version 3's question bank — the opening regularity question, for now.

Every option carries the evidence it encodes to: a ``(μ, σ)`` pair *before* the
irreducible self-report bias is folded in. The bias is added by the engine, in
quadrature, on every answer alike — that is what makes under-reporting no more
profitable than over-reporting, and what makes the value of each extra question
decay to zero on its own.

The opening "I have never played" anchor is the one option verified by hand
against the published beginner result; the rest are hypotheses like every
constant in the engine, to be falsified against the ratings they generate.
"""

from __future__ import annotations

from app.engines.assessment import AnswerOption, AnsweredQuestion, Question
from app.kernel import Sport

OPENING_QUESTION_ID = "opening.regularity"
NEVER_PLAYED_OPTION_ID = "never-played"

# option id -> (μ, σ) evidence, before the self-report bias is combined in.
_REGULARITY_EVIDENCE: dict[str, tuple[float, float]] = {
    NEVER_PLAYED_OPTION_ID: (1.20, 0.75),
    "tried-a-few-times": (1.80, 0.90),
    "occasional": (2.60, 0.90),
    "regular": (3.30, 0.85),
    "frequent": (3.90, 0.85),
}

# A plain noun for each sport, so the copy reads naturally. The registry enum is
# uppercase; the questionnaire speaks to a person.
_SPORT_NOUN: dict[Sport, str] = {
    Sport.PADEL: "padel",
    Sport.TENNIS: "tennis",
    Sport.SQUASH: "squash",
    Sport.BADMINTON: "badminton",
}


def opening_question(sport: Sport) -> Question:
    """The regularity question that opens every assessment, situation first."""

    noun = _SPORT_NOUN[sport]
    return Question(
        id=OPENING_QUESTION_ID,
        category="Playing regularly",
        situation=f"To start, think about how {noun} fits into your life these days.",
        text=f"How often do you play {noun}?",
        qualifier="Choose the option that fits best.",
        tier=None,
        options=(
            AnswerOption(NEVER_PLAYED_OPTION_ID, "I have never played"),
            AnswerOption("tried-a-few-times", "I've played a handful of times"),
            AnswerOption("occasional", "I play now and then"),
            AnswerOption("regular", "I play most weeks"),
            AnswerOption("frequent", "I play several times a week"),
        ),
    )


def raw_evidence_for(answered: AnsweredQuestion) -> tuple[float, float] | None:
    """The ``(μ, σ)`` an answer encodes to, or ``None`` if it is not recognised."""

    if answered.question_id != OPENING_QUESTION_ID:
        return None
    return _REGULARITY_EVIDENCE.get(answered.option_id)
