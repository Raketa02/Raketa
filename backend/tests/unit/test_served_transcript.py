"""The served Transcript: answers reproduced with the copy they were asked with.

The stream stores two ids per answer. What a client needs to *render* an answered
question is the whole question, so the copy is reproduced by asking the engine
what it would have put to a player who had answered the first *n* answers — the
same determinism the outstanding question already rests on, pointed backwards.

The tests below are of the derivation and of the mapper that puts it on the wire.
Nothing here fakes the engine except where the point *is* that the engine
disagrees: a stub deciding which question comes next would be a test of the stub.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.engines.assessment import (
    AnswerOption,
    AskQuestion,
    AssessmentResult,
    BandView,
    Complete,
    Question,
    Step,
    Transcript,
)
from app.engines.racketskill.v3 import RacketSkillEngineV3
from app.engines.racketskill.v3.questions import NEVER_PLAYED_OPTION_ID
from app.kernel import Sport
from app.modules.rating.application.assessment_view import (
    current_step,
    served_transcript,
)
from app.modules.rating.domain.assessment import Assessment
from app.modules.rating.presentation.schemas import AssessmentStepResponse

NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)
SPORT = Sport.PADEL


def _run(engine, *, answers: int | None = None, option: int = -1) -> Assessment:
    """A run driven by the engine, as the use cases drive it, then replayed.

    ``answers`` stops it early — a run still in progress, which is the state the
    Transcript exists to serve. Left off, it answers until the engine stops.
    """

    assessment = Assessment.start(
        assessment_id=uuid4(),
        player_id=uuid4(),
        sport=SPORT,
        engine_version=engine.version,
        occurred_at=NOW,
    )
    while answers is None or len(assessment.transcript) < answers:
        step = engine.next_step(sport=SPORT, transcript=assessment.transcript)
        if not isinstance(step, AskQuestion):
            break
        assessment.ask(
            question_id=step.question.id,
            reason=step.reason,
            mu=step.mu,
            sigma=step.sigma,
            occurred_at=NOW,
        )
        assessment.answer(
            question_id=step.question.id,
            option_id=step.question.options[option].id,
            occurred_at=NOW,
        )
    return Assessment.from_history(assessment.pull_events())


def _complete(engine, assessment: Assessment) -> Assessment:
    """Finish a run the way ``SubmitAnswer`` finishes one, on the same aggregate."""

    stop = engine.next_step(sport=SPORT, transcript=assessment.transcript)
    assert isinstance(stop, Complete)
    assessment.complete(
        result=engine.finalize(sport=SPORT, transcript=assessment.transcript),
        stop=stop,
        occurred_at=NOW,
    )
    return assessment


# --- What it reproduces ---------------------------------------------------------


def test_a_run_with_no_answers_yet_serves_an_empty_transcript() -> None:
    engine = RacketSkillEngineV3()
    assessment = _run(engine, answers=0)

    # Empty rather than absent: a client reads one shape on every step, and
    # "nothing answered yet" is a length, not a missing field.
    assert served_transcript(engine, assessment) == ()


def test_every_answer_is_served_with_the_question_it_answered() -> None:
    engine = RacketSkillEngineV3()
    assessment = _run(engine, answers=4)

    entries = served_transcript(engine, assessment)

    assert len(entries) == 4
    assert [entry.question.id for entry in entries] == [
        answered.question_id for answered in assessment.transcript
    ]
    assert [entry.option_id for entry in entries] == [
        answered.option_id for answered in assessment.transcript
    ]


def test_an_entry_carries_the_question_as_it_was_asked() -> None:
    engine = RacketSkillEngineV3()
    assessment = _run(engine, answers=1)

    (entry,) = served_transcript(engine, assessment)
    opening = engine.next_step(sport=SPORT, transcript=())
    assert isinstance(opening, AskQuestion)

    # The whole question, not a summary of it — an id could not be rendered by a
    # client that has never been shown this question, which is every client
    # resuming a run on a fresh install.
    assert entry.question == opening.question
    assert entry.question.category and entry.question.situation
    assert entry.question.text and entry.question.qualifier
    assert len(entry.question.options) == 5
    assert entry.option_id in {option.id for option in entry.question.options}


def test_the_chosen_option_is_the_one_the_player_chose() -> None:
    engine = RacketSkillEngineV3()
    # Position 0 rather than the -1 every other helper takes, so an entry that
    # simply echoed the first option would pass nothing here.
    assessment = _run(engine, answers=3, option=0)

    entries = served_transcript(engine, assessment)

    assert [entry.option_id for entry in entries] == [
        entry.question.options[0].id for entry in entries
    ]


def test_the_transcript_grows_by_one_entry_per_answer() -> None:
    engine = RacketSkillEngineV3()

    for answered in range(0, 5):
        assessment = _run(engine, answers=answered)
        assert len(served_transcript(engine, assessment)) == answered


def test_a_finished_run_still_serves_the_evidence_it_was_rated_on() -> None:
    engine = RacketSkillEngineV3()
    assessment = _complete(engine, _run(engine))  # answered to the stop

    entries = served_transcript(engine, assessment)

    assert assessment.result is not None
    assert len(entries) == assessment.result.questions_asked


def test_the_beginner_serves_the_single_answer_that_ended_the_run() -> None:
    engine = RacketSkillEngineV3()
    assessment = Assessment.start(
        assessment_id=uuid4(),
        player_id=uuid4(),
        sport=SPORT,
        engine_version=engine.version,
        occurred_at=NOW,
    )
    opening = engine.next_step(sport=SPORT, transcript=())
    assert isinstance(opening, AskQuestion)
    assessment.ask(
        question_id=opening.question.id, reason="", mu=0.0, sigma=0.0, occurred_at=NOW
    )
    assessment.answer(
        question_id=opening.question.id,
        option_id=NEVER_PLAYED_OPTION_ID,
        occurred_at=NOW,
    )

    replayed = Assessment.from_history(assessment.pull_events())
    (entry,) = served_transcript(engine, replayed)

    assert entry.question.id == opening.question.id
    assert entry.option_id == NEVER_PLAYED_OPTION_ID


# --- What it does when the engine cannot answer for the run ---------------------


class _DisagreeingEngine:
    """An engine that reproduces a prefix and then asks something else.

    Which is what a *retired* engine version looks like from here: the run was
    driven by an engine this process no longer has, so replay is only guaranteed
    to agree for as long as the two versions happen to route alike.
    """

    def __init__(self, real: RacketSkillEngineV3, *, agrees_for: int) -> None:
        self._real = real
        self._agrees_for = agrees_for

    @property
    def version(self) -> str:
        return "disagreeing.v1"

    def next_step(self, *, sport: Sport, transcript: Transcript) -> Step:
        if len(transcript) >= self._agrees_for:
            return AskQuestion(
                question=Question(
                    id="somebody.else.would.have.asked.this",
                    category="c",
                    situation="s",
                    text="t",
                    qualifier="q",
                    options=(AnswerOption(id="o", text="o"),),
                ),
                reason="r",
                mu=2.6,
                sigma=2.6,
            )
        return self._real.next_step(sport=sport, transcript=transcript)

    def finalize(self, *, sport: Sport, transcript: Transcript) -> AssessmentResult:
        return self._real.finalize(sport=sport, transcript=transcript)


class _StoppingEngine(_DisagreeingEngine):
    """The other way a retired engine fails to reproduce: it stops sooner."""

    def next_step(self, *, sport: Sport, transcript: Transcript) -> Step:
        if len(transcript) >= self._agrees_for:
            return Complete(reason="stop", value=0.0)
        return self._real.next_step(sport=sport, transcript=transcript)


def test_a_question_the_engine_no_longer_asks_ends_the_transcript() -> None:
    real = RacketSkillEngineV3()
    assessment = _run(real, answers=4)

    entries = served_transcript(_DisagreeingEngine(real, agrees_for=2), assessment)

    # Two entries, not four and not an exception: there is nothing truthful to
    # serve past the point the two engines part company, so it ends there rather
    # than claiming this player was asked a question they never saw.
    assert len(entries) == 2
    assert [entry.question.id for entry in entries] == [
        answered.question_id for answered in assessment.transcript[:2]
    ]


def test_an_engine_that_stops_sooner_ends_the_transcript_too() -> None:
    real = RacketSkillEngineV3()
    assessment = _run(real, answers=4)

    entries = served_transcript(_StoppingEngine(real, agrees_for=3), assessment)

    assert len(entries) == 3


def test_a_disagreement_leaves_the_rest_of_the_step_intact() -> None:
    # The transcript is the part that cannot be reproduced. The count is replayed
    # from the stream and owes the engine nothing, so it still reports the truth.
    real = RacketSkillEngineV3()
    assessment = _run(real, answers=4)

    step = current_step(_DisagreeingEngine(real, agrees_for=2), assessment)

    assert step.questions_asked == 4
    assert len(step.transcript) == 2


# --- The wire mapper ------------------------------------------------------------


def test_the_step_response_carries_every_entry_in_order() -> None:
    engine = RacketSkillEngineV3()
    assessment = _run(engine, answers=3)

    step = current_step(engine, assessment)
    body = AssessmentStepResponse.from_step(step).model_dump()

    assert [entry["question"]["id"] for entry in body["transcript"]] == [
        answered.question_id for answered in assessment.transcript
    ]
    assert [entry["option_id"] for entry in body["transcript"]] == [
        answered.option_id for answered in assessment.transcript
    ]
    first = body["transcript"][0]["question"]
    assert set(first) == {
        "id",
        "category",
        "tier",
        "situation",
        "text",
        "qualifier",
        "options",
    }


def test_the_step_response_carries_an_empty_list_rather_than_omitting_it() -> None:
    engine = RacketSkillEngineV3()
    assessment = _run(engine, answers=0)

    step = current_step(engine, assessment)
    body = AssessmentStepResponse.from_step(step).model_dump()

    assert "transcript" in body
    assert body["transcript"] == []


def test_an_abandoned_run_still_serves_what_was_answered_before_it_ended() -> None:
    engine = RacketSkillEngineV3()
    assessment = _run(engine, answers=2)
    assessment.abandon(occurred_at=NOW)

    step = current_step(engine, assessment)

    assert step.status == "abandoned"
    assert step.question is None
    assert len(step.transcript) == 2


def test_a_completed_step_carries_its_transcript_beside_its_result() -> None:
    engine = RacketSkillEngineV3()
    assessment = _complete(engine, _run(engine))

    step = current_step(engine, assessment)

    assert step.result is not None
    assert len(step.transcript) == step.questions_asked
    assert isinstance(step.result.band, BandView)  # the result is untouched by this
