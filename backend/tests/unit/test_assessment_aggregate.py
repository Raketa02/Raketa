"""The Assessment aggregate — replay reproduces the transcript, and the
outstanding-question invariant holds.

Revision is the second half of that: the stream only ever grows, and replaying a
revision **shortens the projection** rather than editing anything already on it.
The two facts are asserted together on purpose — a truncation that lost the event
would pass every transcript assertion here and quietly destroy the record."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.engines.assessment import (
    CALIBRATION_PRIORITY_STANDARD,
    AnsweredQuestion,
    AssessmentResult,
    BandView,
    Complete,
)
from app.engines.racketskill.v3 import RacketSkillEngineV3
from app.kernel import Sport
from app.modules.rating.application.assessment_view import completed_result
from app.modules.rating.domain.assessment import Assessment
from app.modules.rating.domain.errors import (
    AssessmentAlreadyFinished,
    QuestionNotOutstanding,
)
from app.modules.rating.domain.events import (
    AnswerRevised,
    AnswerSubmitted,
    AssessmentCompleted,
)

NOW = datetime(2026, 8, 13, tzinfo=timezone.utc)


def _result() -> AssessmentResult:
    return AssessmentResult(
        mu=1.40,
        sigma=0.9821,
        confidence=18,
        range_low=1.0,
        range_high=2.38,
        band=BandView(name="New", lower=1.0, upper=2.0),
        status="Initial Estimate",
        questions_asked=1,
        engine_version="racketskill-fusion-v3",
    )


def _stop() -> Complete:
    return Complete(reason="beginner-fast-path", value=0.0)


def _started() -> Assessment:
    assessment = Assessment.start(
        assessment_id=uuid4(),
        player_id=uuid4(),
        sport=Sport.PADEL,
        engine_version="racketskill-fusion-v3",
        occurred_at=NOW,
    )
    assessment.ask(
        question_id="opening.regularity",
        reason="opening",
        mu=2.6,
        sigma=2.6,
        occurred_at=NOW,
    )
    return assessment


def test_replay_reproduces_transcript_and_result() -> None:
    assessment = _started()
    assessment.answer(
        question_id="opening.regularity", option_id="never-played", occurred_at=NOW
    )
    assessment.complete(result=_result(), stop=_stop(), occurred_at=NOW)

    replayed = Assessment.from_history(assessment.pull_events())

    assert replayed.transcript == (
        AnsweredQuestion("opening.regularity", "never-played"),
    )
    assert replayed.is_completed
    assert replayed.result == _result()
    assert replayed.version == assessment.version


def test_answer_is_rejected_when_not_outstanding() -> None:
    assessment = _started()
    with pytest.raises(QuestionNotOutstanding):
        assessment.answer(
            question_id="some.other.question", option_id="x", occurred_at=NOW
        )


def test_a_completed_assessment_rejects_further_answers() -> None:
    assessment = _started()
    assessment.answer(
        question_id="opening.regularity", option_id="never-played", occurred_at=NOW
    )
    assessment.complete(result=_result(), stop=_stop(), occurred_at=NOW)
    with pytest.raises(QuestionNotOutstanding):
        assessment.answer(
            question_id="opening.regularity",
            option_id="never-played",
            occurred_at=NOW,
        )


def test_abandonment_ends_the_stream_and_survives_replay() -> None:
    assessment = _started()
    assessment.abandon(occurred_at=NOW)

    replayed = Assessment.from_history(assessment.pull_events())

    assert replayed.is_abandoned
    assert not replayed.is_in_progress
    assert replayed.outstanding_question_id is None


def test_an_abandoned_assessment_rejects_further_answers() -> None:
    assessment = _started()
    assessment.abandon(occurred_at=NOW)
    with pytest.raises(QuestionNotOutstanding):
        assessment.answer(
            question_id="opening.regularity",
            option_id="never-played",
            occurred_at=NOW,
        )


def test_abandoning_twice_is_a_no_op() -> None:
    assessment = _started()
    assessment.abandon(occurred_at=NOW)
    assessment.pull_events()

    assessment.abandon(occurred_at=NOW)

    assert assessment.pull_events() == []


def test_a_completed_assessment_cannot_be_abandoned() -> None:
    assessment = _started()
    assessment.answer(
        question_id="opening.regularity", option_id="never-played", occurred_at=NOW
    )
    assessment.complete(result=_result(), stop=_stop(), occurred_at=NOW)
    with pytest.raises(AssessmentAlreadyFinished):
        assessment.abandon(occurred_at=NOW)


# --- Revising: the stream grows, the transcript shortens -------------------------


def _answered(*pairs: tuple[str, str]) -> Assessment:
    """A run that asked and answered each pair, in order."""

    assessment = Assessment.start(
        assessment_id=uuid4(),
        player_id=uuid4(),
        sport=Sport.PADEL,
        engine_version="racketskill-fusion-v3",
        occurred_at=NOW,
    )
    for question_id, option_id in pairs:
        assessment.ask(
            question_id=question_id, reason="test", mu=2.6, sigma=2.6, occurred_at=NOW
        )
        assessment.answer(question_id=question_id, option_id=option_id, occurred_at=NOW)
    return assessment


def test_revising_truncates_the_transcript_at_the_revised_question() -> None:
    assessment = _answered(("q1", "a"), ("q2", "b"), ("q3", "c"))

    assessment.revise(question_id="q2", option_id="B", occurred_at=NOW)

    # q3's answer is gone: it was pitched at a difficulty chosen from the estimate
    # q2's old answer produced, so keeping it would mean something never said.
    assert assessment.transcript == (
        AnsweredQuestion("q1", "a"),
        AnsweredQuestion("q2", "B"),
    )
    assert assessment.last_answered_question_id == "q2"
    # The outstanding question was chosen from the estimate as it stood; there is
    # nothing to answer until the engine is asked again.
    assert assessment.outstanding_question_id is None


def test_the_revision_is_appended_and_nothing_earlier_is_removed() -> None:
    # The load-bearing half. "A revision shortens the past; it never edits it" is
    # a statement about the *stream*, and the truncated transcript above is
    # exactly what a wrong implementation would also produce.
    assessment = _answered(("q1", "a"), ("q2", "b"), ("q3", "c"))

    assessment.revise(question_id="q2", option_id="B", occurred_at=NOW)

    recorded = assessment.pull_events()
    answers = [event for event in recorded if isinstance(event, AnswerSubmitted)]
    assert [(event.question_id, event.option_id) for event in answers] == [
        ("q1", "a"),
        ("q2", "b"),
        ("q3", "c"),
    ]
    assert isinstance(recorded[-1], AnswerRevised)
    assert (recorded[-1].question_id, recorded[-1].option_id) == ("q2", "B")


def test_a_revision_survives_replay() -> None:
    assessment = _answered(("q1", "a"), ("q2", "b"), ("q3", "c"))
    assessment.revise(question_id="q2", option_id="B", occurred_at=NOW)

    replayed = Assessment.from_history(assessment.pull_events())

    assert replayed.transcript == assessment.transcript
    assert replayed.version == assessment.version
    assert replayed.last_answered_question_id == "q2"
    assert replayed.outstanding_question_id is None


def test_revising_the_first_answer_from_deep_in_a_run_leaves_one_answer() -> None:
    assessment = _answered(("q1", "a"), ("q2", "b"), ("q3", "c"), ("q4", "d"))

    assessment.revise(question_id="q1", option_id="A", occurred_at=NOW)

    assert assessment.transcript == (AnsweredQuestion("q1", "A"),)


def test_revising_repeatedly_replays_to_the_last_word() -> None:
    assessment = _answered(("q1", "a"), ("q2", "b"))
    assessment.revise(question_id="q2", option_id="B", occurred_at=NOW)
    assessment.ask(question_id="q3", reason="test", mu=2.6, sigma=2.6, occurred_at=NOW)
    assessment.answer(question_id="q3", option_id="c", occurred_at=NOW)

    assessment.revise(question_id="q1", option_id="A", occurred_at=NOW)

    replayed = Assessment.from_history(assessment.pull_events())
    assert replayed.transcript == (AnsweredQuestion("q1", "A"),)


def test_re_selecting_the_recorded_option_records_nothing() -> None:
    # Changing your mind and changing it back is not a decision the stream needs,
    # and a revision that revised nothing would still truncate — discarding later
    # answers the player never asked to lose. Same no-op shape as ``abandon``.
    assessment = _answered(("q1", "a"), ("q2", "b"))
    assessment.pull_events()

    assessment.revise(question_id="q1", option_id="a", occurred_at=NOW)

    assert assessment.pull_events() == []
    assert assessment.transcript == (
        AnsweredQuestion("q1", "a"),
        AnsweredQuestion("q2", "b"),
    )


def test_a_question_that_was_never_answered_is_not_revisable() -> None:
    assessment = _answered(("q1", "a"))
    with pytest.raises(QuestionNotOutstanding):
        assessment.revise(question_id="q9", option_id="x", occurred_at=NOW)


def test_a_completed_run_rejects_a_revision() -> None:
    assessment = _answered(("opening.regularity", "never-played"))
    assessment.complete(result=_result(), stop=_stop(), occurred_at=NOW)
    with pytest.raises(QuestionNotOutstanding):
        assessment.revise(
            question_id="opening.regularity", option_id="frequent", occurred_at=NOW
        )


def test_an_abandoned_run_rejects_a_revision() -> None:
    assessment = _answered(("q1", "a"))
    assessment.abandon(occurred_at=NOW)
    with pytest.raises(QuestionNotOutstanding):
        assessment.revise(question_id="q1", option_id="b", occurred_at=NOW)


def test_the_recorded_option_is_what_separates_an_answer_from_a_change() -> None:
    assessment = _answered(("q1", "a"), ("q2", "b"))
    assessment.ask(question_id="q3", reason="test", mu=2.6, sigma=2.6, occurred_at=NOW)

    assert assessment.recorded_option("q1") == "a"
    assert assessment.recorded_option("q2") == "b"
    # Outstanding, so unanswered: a submission for it is an answer, not a change.
    assert assessment.recorded_option("q3") is None
    assert assessment.recorded_option("q9") is None


# --- The recorded result, and the explanation reproduced from the transcript ----


def _completed_from(
    engine,
    transcript: tuple[AnsweredQuestion, ...],
    stop: Complete | None = None,
) -> Assessment:
    """An assessment driven to completion by the engine, as the use case does.

    The transcripts here are hand-built fixtures chosen for what they say about
    the *result*, and the engine would have gone on asking after several of them,
    so the stop defaults to a fixture. A test that means something by the stop
    passes the engine's own step instead.
    """

    assessment = Assessment.start(
        assessment_id=uuid4(),
        player_id=uuid4(),
        sport=Sport.PADEL,
        engine_version=engine.version,
        occurred_at=NOW,
    )
    for entry in transcript:
        assessment.ask(
            question_id=entry.question_id,
            reason="test",
            mu=2.6,
            sigma=2.6,
            occurred_at=NOW,
        )
        assessment.answer(
            question_id=entry.question_id, option_id=entry.option_id, occurred_at=NOW
        )
    assessment.complete(
        result=engine.finalize(sport=Sport.PADEL, transcript=assessment.transcript),
        stop=stop or _stop(),
        occurred_at=NOW,
    )
    return Assessment.from_history(assessment.pull_events())


def test_the_stream_records_the_facts_and_not_the_copy() -> None:
    # A completion records why confidence landed where it did, as a key. The
    # sentence that key selects is copy: it is reproduced, never stored, so
    # rewording it is not a migration.
    engine = RacketSkillEngineV3()
    replayed = _completed_from(
        engine, (AnsweredQuestion("opening.regularity", "never-played"),)
    )
    recorded = replayed.result
    assert recorded is not None
    assert recorded.calibration_priority == CALIBRATION_PRIORITY_STANDARD
    assert recorded.confidence_reason is None  # copy is not replayed
    assert recorded.factors == ()
    # Nor is the ceiling: what a questionnaire could prove belongs to the engine
    # version that ran it, and the stream records the rating rather than the
    # engine. Every served result gets it back from the engine that is asked.
    assert recorded.confidence_ceiling is None


def test_the_reproduced_explanation_agrees_with_the_recorded_numbers() -> None:
    # The explanation is derived rather than stored, so this is the guarantee
    # that makes that safe: the numbers a client is served are, to the digit, the
    # numbers on the stream. A card can never print a band that disagrees with
    # the level beside it, because there is only ever one computation.
    engine = RacketSkillEngineV3()
    transcript = (
        AnsweredQuestion("opening.regularity", "frequent"),
        AnsweredQuestion("context.environment", "env3"),
        AnsweredQuestion("context.relative", "r3"),
        AnsweredQuestion("execution.basic", "e0"),
        AnsweredQuestion("execution.standard", "e0"),
    )
    replayed = _completed_from(engine, transcript)
    recorded = replayed.result
    served = completed_result(engine, replayed)
    assert recorded is not None and served is not None

    assert (served.mu, served.sigma, served.confidence) == (
        recorded.mu,
        recorded.sigma,
        recorded.confidence,
    )
    assert served.band == recorded.band
    assert (served.range_low, served.range_high) == (
        recorded.range_low,
        recorded.range_high,
    )
    assert served.calibration_priority == recorded.calibration_priority
    # And the explanation the recorded result cannot carry is there, the ceiling
    # among it: the engine that is asked answers for what it can prove, so the
    # number and the ceiling it is read against always come from one engine.
    assert served.factors and served.confidence_reason is not None
    assert served.confidence_ceiling is not None
    assert served.confidence <= served.confidence_ceiling


def test_a_result_from_a_retired_engine_keeps_its_number_and_loses_its_commentary() -> (
    None
):
    # A later version would explain the transcript its own way, which is not what
    # the player was shown. The recorded result stands, unexplained, rather than
    # acquiring commentary that was never true of it.
    engine = RacketSkillEngineV3()
    replayed = _completed_from(
        engine, (AnsweredQuestion("opening.regularity", "never-played"),)
    )
    replayed.engine_version = "racketskill-fusion-v4"

    served = completed_result(engine, replayed)
    assert served == replayed.result
    assert served is not None and served.factors == ()
    # Including the ceiling, which is why the field is optional on the wire. The
    # ceiling in force is v4's, and this rating is not v4's; serving the current
    # engine's number here would say a v3 rating was measured against a limit
    # that did not exist when it was produced. A client shows no tick instead —
    # the same thing it already does with the missing confidence sentence.
    assert served.confidence_ceiling is None


# --- The stop: the one routing decision that used to go unrecorded --------------


def test_the_stop_survives_replay_with_the_engine_s_own_reason_and_value() -> None:
    # Every question this aggregate asked records why it was asked; the moment it
    # decided to ask no more must be answerable the same way, from the stream
    # alone and without re-running the engine.
    engine = RacketSkillEngineV3()
    transcript = (AnsweredQuestion("opening.regularity", "never-played"),)
    stop = engine.next_step(sport=Sport.PADEL, transcript=transcript)
    assert isinstance(stop, Complete)  # the fast path really does end here

    replayed = _completed_from(engine, transcript, stop=stop)

    assert replayed.stop_reason == stop.reason == "beginner-fast-path"
    assert replayed.stop_value == stop.value == 0.0


def test_a_completion_recorded_before_stops_were_recorded_replays_without_one() -> None:
    # The fields carry defaults rather than a new catalog version, so history
    # written before them decodes unchanged. On such a run the absence dates the
    # row — completed before stops were recorded — and is never "we do not know".
    assessment = _started()
    assessment.answer(
        question_id="opening.regularity", option_id="never-played", occurred_at=NOW
    )
    result = _result()
    replayed = Assessment.from_history(
        [
            *assessment.pull_events(),
            AssessmentCompleted(
                assessment_id=assessment.id,
                mu=result.mu,
                sigma=result.sigma,
                confidence=result.confidence,
                range_low=result.range_low,
                range_high=result.range_high,
                band_name=result.band.name,
                band_lower=result.band.lower,
                band_upper=result.band.upper,
                status=result.status,
                questions_asked=result.questions_asked,
                engine_version=result.engine_version,
                occurred_at=NOW,
            ),
        ]
    )

    assert replayed.is_completed
    assert replayed.result == result
    assert replayed.stop_reason is None
    assert replayed.stop_value is None
