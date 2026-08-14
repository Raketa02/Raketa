"""The six golden personas — **this file is meant to break on a constant retune.**

That is the point of it, and why it is kept apart from the invariant tests. Every
constant in the engine is an admitted hypothesis with a measurement that would
falsify it; when one is retuned these numbers *should* move, and updating them
should be a deliberate act with a reason, not a red diff to make green.

The invariants that must survive a retune live in the other engine test modules.
Nothing here is an invariant — it is a snapshot of what the current constants
produce for six characteristic players.

Reconciliation against the published figures (issue #10)
--------------------------------------------------------
The source documents publish a result per persona but **not the answer sequences
that produced them**. Only the beginner is exactly reproducible, because there is
exactly one way to be a beginner: the opening question's first option ends the
assessment, so no policy freedom exists. It matches to the digit — 1,40 · 18%.

For the other five the level cannot be reproduced without the original policy, so
the levels below are this engine's, under the explicit policies written here. They
were accepted rather than treated as failures because every property the documents
actually constrain does agree: the band, the 30% ceiling, the question-count range
for the player type, and the ordering of the personas against each other.

One genuine defect was found and fixed rather than baselined. The engine's band
boundaries had been evenly spaced (1–2, 2–3, 3–4, 4–5) where the specification,
``CONTEXT.md`` and the locked design system all give deliberately uneven ones
(1,0–1,5 · 1,6–2,6 · 2,7–3,8 · 3,9–5,0). The advanced persona is what exposed it:
at μ 3,91 the old boundaries banded it *Established* while the published figure
says *Advanced*.

The tier thresholds and the third-demonstration floor had been rounded the same
way. They were *not* corrected with the bands, because unlike the boundaries they
are behavioural — they move which tier a player is asked at, and so what an
answer is worth. They were pinned, and corrected separately in #15.

**Not one number below moved when they were corrected**, which is worth recording
because the expectation was that they would. The corrected constants change the
*order* in which two of these personas are asked their demonstrations, and change
nothing about the set: the same tiers, answered the same way. Fusion is a
precision-weighted product over the whole transcript and so is order-invariant, so
an identical answer set produces an identical result. Verified by diffing every
persona's answer set and routed order across the change, not by the numbers here
happening to stay green.
"""

from collections.abc import Callable

import pytest

from app.engines.assessment import AnsweredQuestion, AskQuestion, Complete, Question
from app.engines.racketskill.v3 import RacketSkillEngineV3
from app.kernel import Sport

#: A policy picks which option to answer a question with, as an index into the
#: question's own options. Indexing by position rather than by option id keeps a
#: policy readable as "how strong an answer is this" and survives copy changes.
Policy = Callable[[Question], int]

OPENING = "opening.regularity"


def _top(question: Question) -> int:
    return len(question.options) - 1


def _run(policy: Policy, sport: Sport = Sport.PADEL) -> tuple:
    """Drive a whole assessment with one policy and finalize it."""

    engine = RacketSkillEngineV3()
    transcript: tuple[AnsweredQuestion, ...] = ()
    while True:
        step = engine.next_step(sport=sport, transcript=transcript)
        if isinstance(step, Complete):
            break
        assert isinstance(step, AskQuestion)
        question = step.question
        index = min(policy(question), len(question.options) - 1)
        transcript += (AnsweredQuestion(question.id, question.options[index].id),)
    return engine.finalize(sport=sport, transcript=transcript)


# --- the six policies, each a plain-language player -------------------------


def _beginner(question: Question) -> int:
    """Has never played. The first option ends it — no technique is ever asked."""

    return 0


def _developing(question: Question) -> int:
    """Plays a little, casually, and lands under half the shots it is asked about."""

    return 1


def _established(question: Question) -> int:
    """Plays most weeks against varied opponents; executes reliably, not brilliantly."""

    return 3 if question.id == OPENING else 2


def _advanced(question: Question) -> int:
    """Plays several times a week in strong matches and executes at the top option."""

    return _top(question)


def _returning(question: Question) -> int:
    """Played well, then stopped: low recent volume and the longest layoff offered."""

    if question.id == "recent.volume":
        return 0
    if question.id.startswith("history.layoff"):
        return _top(question)
    return 2 if question.id == OPENING else 3


def _contradictory(question: Question) -> int:
    """Claims a strong standing, then reports almost never executing.

    Claims (regularity, context) answer near the top; demonstrations (execution,
    tactical) answer at the bottom. The gap is what the tie-breaker is for.
    """

    is_demonstration = question.tier is not None or question.id.startswith("tactical")
    return 0 if is_demonstration else _top(question)


# persona → (policy, mu, sigma, confidence, band, questions asked)
PERSONAS: dict[str, tuple[Policy, float, float, int, str, int]] = {
    "beginner": (_beginner, 1.40, 0.9821, 18, "New", 1),
    "developing": (_developing, 2.39, 0.8400, 30, "Developing", 6),
    "established": (_established, 3.26, 0.8460, 30, "Established", 7),
    "advanced": (_advanced, 3.91, 0.8409, 30, "Advanced", 8),
    "returning": (_returning, 3.34, 0.9042, 25, "Established", 9),
    "contradictory": (_contradictory, 2.61, 1.0337, 14, "Developing", 8),
}


@pytest.mark.parametrize("persona", sorted(PERSONAS))
def test_persona_result_is_exactly_this(persona: str) -> None:
    policy, mu, sigma, confidence, band, asked = PERSONAS[persona]
    result = _run(policy)
    assert (result.mu, result.sigma, result.confidence) == (mu, sigma, confidence)
    assert result.band.name == band
    assert result.questions_asked == asked


def test_beginner_matches_the_published_figure_to_the_digit() -> None:
    """The one persona with no policy freedom, and so the one exact check available."""

    result = _run(_beginner)
    assert (result.mu, result.confidence, result.band.name) == (1.40, 18, "New")
    assert (result.range_low, result.range_high) == (1.00, 2.38)


@pytest.mark.parametrize(
    ("persona", "low", "high"),
    [
        ("beginner", 1, 1),
        ("developing", 5, 6),
        ("established", 6, 7),
        ("advanced", 7, 8),
        ("returning", 8, 9),
        ("contradictory", 8, 9),
    ],
)
def test_question_count_is_in_the_documented_range(
    persona: str, low: int, high: int
) -> None:
    assert low <= _run(PERSONAS[persona][0]).questions_asked <= high


def test_all_four_bands_are_reachable() -> None:
    reached = {_run(PERSONAS[name][0]).band.name for name in PERSONAS}
    assert {"New", "Developing", "Established", "Advanced"} <= reached


def test_personas_are_strictly_ordered_by_level() -> None:
    """A stronger player must not come out below a weaker one."""

    ordered = ["beginner", "developing", "established", "advanced"]
    levels = [_run(PERSONAS[name][0]).mu for name in ordered]
    assert levels == sorted(levels)
    assert len(set(levels)) == len(levels)


def test_an_advanced_player_answers_more_questions_than_a_developing_one() -> None:
    """Bracketing, not a sigma-only rule: extreme answers prove only a floor."""

    assert _run(_advanced).questions_asked > _run(_developing).questions_asked


def test_a_layoff_widens_the_range_without_lowering_the_level() -> None:
    """The returning player is placed above the established one, just less surely."""

    returning, established = _run(_returning), _run(_established)
    assert returning.mu > established.mu
    assert returning.sigma > established.sigma
    assert returning.confidence < established.confidence
