"""The current state of an assessment, derived from its replayed stream.

The client holds no flow state, so every read of an assessment answers the same
question the mutation responses do: *what is the current step* — the outstanding
question, the final result, or neither once it has been abandoned. Because the
engine is deterministic, the outstanding question is reproduced from the answered
transcript rather than stored a second time.

The finished result is reproduced the same way, and for the same reason. Its
numbers are recorded on the stream, but its *explanation* — the factor rows and
the confidence sentence — is copy and computed direction, and storing those would
freeze wording into history and open the door to a card whose rows disagree with
the number above them.
"""

from __future__ import annotations

from app.engines.assessment import (
    AskQuestion,
    AssessmentEngine,
    AssessmentResult,
    Question,
)
from app.modules.rating.application.commands import AssessmentStep, TranscriptEntry
from app.modules.rating.domain.assessment import Assessment


def outstanding_question(engine: AssessmentEngine, assessment: Assessment) -> Question:
    step = engine.next_step(sport=assessment.sport, transcript=assessment.transcript)
    assert isinstance(step, AskQuestion)
    return step.question


def served_transcript(
    engine: AssessmentEngine, assessment: Assessment
) -> tuple[TranscriptEntry, ...]:
    """Every answer given so far, each with the question it answered, in order.

    The stream stores an answer as two ids, because that is all the engine reads.
    A reader that has to *render* an answered question needs its copy, and the
    copy is the engine's — so it is reproduced exactly as the outstanding question
    is: the engine is asked what it would put to a player who had answered the
    first *n* answers, for every *n* the run has. That is the same determinism
    ``outstanding_question`` already rests on, applied to the run's past rather
    than to its present, and it is why the copy is never stored a second time.

    **It stops at the first disagreement instead of asserting.** ``next_step`` is
    only guaranteed to reproduce what was asked while the engine asked is the
    engine that asked it, so a run whose ``engine_version`` has since been retired
    can replay to a question that was never put to this player — or to no question
    at all. There is nothing truthful to serve past that point, and the transcript
    ends there. It is the rule ``completed_result`` already applies to the
    explanation, in the shape a sequence takes: what a retired engine asked is
    part of what only that engine can say.

    A live run therefore always yields its whole transcript, and that is the only
    case any client has ever seen.
    """

    answered = assessment.transcript
    entries: list[TranscriptEntry] = []
    for position, entry in enumerate(answered):
        step = engine.next_step(sport=assessment.sport, transcript=answered[:position])
        if not isinstance(step, AskQuestion) or step.question.id != entry.question_id:
            break
        entries.append(
            TranscriptEntry(question=step.question, option_id=entry.option_id)
        )
    return tuple(entries)


def questions_asked(assessment: Assessment) -> int:
    """How many of this run's questions have been answered.

    The length of the replayed transcript — the same expression, on the same data,
    that the engine puts on a finished result under this name. So the number does
    not jump as a run finishes: it is one quantity at two moments in the run's
    life, which is why it keeps one name.

    Two things it deliberately is not:

    - **Stored.** A counter on the stream would be a second place holding a fact
      the transcript already holds, and the two would disagree the first time
      either moved. It is also what makes the count survive a reinstall: the
      transcript is the only thing that ever did.
    - **Inclusive of the outstanding question.** That question has been put to the
      player but not answered, so mid-run this is the number of answers *behind*
      them and their position is one further along. Counting it would make the
      mid-run number and the finished one describe two different things.
    """

    return len(assessment.transcript)


def completed_result(
    engine: AssessmentEngine, assessment: Assessment
) -> AssessmentResult | None:
    """The explained result of a finished assessment.

    Reproducing it is exact only while the engine that produced it is the engine
    asked: a later version would explain the transcript its own way, which is not
    what the player was shown. So the recorded result stands whenever the
    versions differ, and the explanation is simply absent — a rating from a
    retired engine keeps its number and loses its commentary, rather than
    acquiring commentary that was never true of it.
    """

    recorded = assessment.result
    if recorded is None or assessment.engine_version != engine.version:
        return recorded
    return engine.finalize(sport=assessment.sport, transcript=assessment.transcript)


def current_step(engine: AssessmentEngine, assessment: Assessment) -> AssessmentStep:
    answered = questions_asked(assessment)
    transcript = served_transcript(engine, assessment)
    if assessment.is_completed:
        return AssessmentStep(
            assessment_id=assessment.id,
            status=assessment.status.value,
            questions_asked=answered,
            transcript=transcript,
            question=None,
            result=completed_result(engine, assessment),
        )
    if assessment.is_abandoned:
        return AssessmentStep(
            assessment_id=assessment.id,
            status=assessment.status.value,
            questions_asked=answered,
            transcript=transcript,
            question=None,
            result=None,
        )
    return AssessmentStep(
        assessment_id=assessment.id,
        status=assessment.status.value,
        questions_asked=answered,
        transcript=transcript,
        question=outstanding_question(engine, assessment),
        result=None,
    )
