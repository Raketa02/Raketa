"""Answering, revising, and the ways a submission can be refused or ignored.

Idempotency comes from the domain, not a header. What a submission *means* is
decided by what the transcript already holds: an answer for the outstanding
question, a **revision** for a question already answered with a different option,
and a replay — recording nothing — for one answered with the same option.
Anything else conflicts. Completion writes two streams in one transaction, which
is the assertion this file exists for — it was reachable only through HTTP over
SQLite before the repository.

Completion also records **why the questionnaire stopped**. Nothing serves it, and
that is deliberate: a decision never recorded cannot be recovered later, so it is
written from the day it ships rather than from the day something reads it.
"""

from __future__ import annotations

from uuid import UUID

import pytest

from app.application.events.store import EventStreamVersionConflict
from app.engines.racketskill.v3.engine import (
    MIN_MARGINAL_GAIN,
    STOP_BEGINNER,
    STOP_MARGINAL,
)
from app.engines.racketskill.v3.questions import NEVER_PLAYED_OPTION_ID
from app.kernel import Sport
from app.modules.rating.application.commands import (
    AssessmentStep,
    SubmitAnswerCommand,
    TranscriptEntry,
)
from app.modules.rating.domain.assessment import Assessment
from app.modules.rating.domain.errors import (
    AnswerNoLongerRevisable,
    AssessmentNotFound,
    InvalidAnswerOption,
    QuestionNotOutstanding,
)
from app.modules.rating.domain.events import (
    AnswerRevised,
    AnswerSubmitted,
    AssessmentCompleted,
    QuestionAsked,
    RatingInitialised,
)
from app.modules.rating.domain.ids import skill_rating_id
from app.modules.rating.infrastructure.event_sourced_assessment_repository import (
    ASSESSMENT_AGGREGATE,
)
from app.modules.rating.infrastructure.event_sourced_skill_rating_repository import (
    RATING_AGGREGATE,
)
from app.shared.ids import new_uuid
from tests.unit.assessment_requests import (
    Request,
    answer,
    request,
    run_to_result,
    start,
)
from tests.unit.fake_event_store import InMemoryEventStore, utc


async def test_answering_records_the_answer_and_the_next_question() -> None:
    store = InMemoryEventStore()
    player_id = new_uuid()
    opening = (await start(store, player_id)).step
    assert opening.question is not None

    call = request(store)
    next_step = await call.submit.execute(
        SubmitAnswerCommand(
            player_id=player_id,
            assessment_id=opening.assessment_id,
            question_id=opening.question.id,
            option_id=opening.question.options[-1].id,
        )
    )

    assert next_step.question is not None
    assert next_step.question.id != opening.question.id
    # The answer just recorded is in the transcript, so the count already has it.
    assert next_step.questions_asked == 1
    assert [type(event) for event in call.events.published] == [
        AnswerSubmitted,
        QuestionAsked,
    ]
    assert call.uow.commits == 1


async def test_replaying_the_just_answered_question_records_nothing() -> None:
    # A response lost in flight is retried by the client with the question it
    # last saw. It must land on the same state, not a second answer.
    store = InMemoryEventStore()
    player_id = new_uuid()
    opening = (await start(store, player_id)).step
    assert opening.question is not None
    after = await answer(store, player_id, opening)

    store.appends = 0
    replay = request(store)
    again = await replay.submit.execute(
        SubmitAnswerCommand(
            player_id=player_id,
            assessment_id=opening.assessment_id,
            question_id=opening.question.id,
            option_id=opening.question.options[-1].id,
        )
    )

    assert again.question is not None and after.question is not None
    assert again.question.id == after.question.id
    assert again.questions_asked == after.questions_asked
    assert store.appends == 0
    assert replay.events.published == []
    assert replay.uow.commits == 0


async def test_a_question_that_is_not_outstanding_conflicts() -> None:
    store = InMemoryEventStore()
    player_id = new_uuid()
    opening = (await start(store, player_id)).step
    assert opening.question is not None

    call = request(store)
    with pytest.raises(QuestionNotOutstanding):
        await call.submit.execute(
            SubmitAnswerCommand(
                player_id=player_id,
                assessment_id=opening.assessment_id,
                question_id="some.other.question",
                option_id=opening.question.options[0].id,
            )
        )

    assert call.events.published == []
    assert call.uow.commits == 0


async def test_a_stale_answer_to_a_finished_run_conflicts() -> None:
    # A finished run has no outstanding question, and reproducing one means
    # asking the engine for a step it will not give: the use case must refuse
    # before it gets there, or a late retry from a client that missed the result
    # surfaces as a crash rather than a conflict.
    #
    # Which conflict depends on whether the run answered that question. This one
    # never did, so there is a question the client could refetch and re-render;
    # ``opening.regularity`` on the same run is the other case, below.
    store = InMemoryEventStore()
    player_id = new_uuid()
    final, _ = await run_to_result(store, player_id)

    call = request(store)
    with pytest.raises(QuestionNotOutstanding):
        await call.submit.execute(
            SubmitAnswerCommand(
                player_id=player_id,
                assessment_id=final.assessment_id,
                question_id="some.question.this.run.never.asked",
                option_id="weekly",
            )
        )

    assert call.uow.commits == 0


async def test_an_option_the_question_does_not_offer_is_rejected() -> None:
    store = InMemoryEventStore()
    player_id = new_uuid()
    opening = (await start(store, player_id)).step
    assert opening.question is not None

    call = request(store)
    with pytest.raises(InvalidAnswerOption):
        await call.submit.execute(
            SubmitAnswerCommand(
                player_id=player_id,
                assessment_id=opening.assessment_id,
                question_id=opening.question.id,
                option_id="not-an-option",
            )
        )

    assert call.events.published == []
    assert call.uow.commits == 0


async def test_another_players_assessment_is_not_found() -> None:
    store = InMemoryEventStore()
    player_id = new_uuid()
    opening = (await start(store, player_id)).step
    assert opening.question is not None

    call = request(store)
    with pytest.raises(AssessmentNotFound):
        await call.submit.execute(
            SubmitAnswerCommand(
                player_id=new_uuid(),
                assessment_id=opening.assessment_id,
                question_id=opening.question.id,
                option_id=opening.question.options[0].id,
            )
        )

    assert call.uow.commits == 0


async def test_an_absent_assessment_is_not_found() -> None:
    store = InMemoryEventStore()
    call = request(store)

    with pytest.raises(AssessmentNotFound):
        await call.submit.execute(
            SubmitAnswerCommand(
                player_id=new_uuid(),
                assessment_id=new_uuid(),
                question_id="opening.regularity",
                option_id="weekly",
            )
        )

    assert call.uow.commits == 0


async def test_completing_writes_both_streams_in_one_transaction() -> None:
    store = InMemoryEventStore()
    player_id = new_uuid()

    final, completing = await run_to_result(store, player_id, Sport.PADEL)

    assert final.question is None and final.result is not None

    assessment_stream = await store.load_stream(
        aggregate_type=ASSESSMENT_AGGREGATE, aggregate_id=final.assessment_id
    )
    assert isinstance(assessment_stream[-1].event, AssessmentCompleted)

    rating_stream = await store.load_stream(
        aggregate_type=RATING_AGGREGATE,
        aggregate_id=skill_rating_id(player_id, Sport.PADEL),
    )
    assert [type(record.event) for record in rating_stream] == [RatingInitialised]

    # One transaction for two aggregates, and the assessment's events reach the
    # outbox before the rating's — the order they happened in.
    assert completing.uow.commits == 1
    assert [type(event) for event in completing.events.published] == [
        AnswerSubmitted,
        AssessmentCompleted,
        RatingInitialised,
    ]


async def test_the_recorded_rating_is_the_result_the_player_was_shown() -> None:
    # Two streams written from one engine call, so a rating cannot describe a
    # different run from the one the response reported.
    store = InMemoryEventStore()
    player_id = new_uuid()

    final, _ = await run_to_result(store, player_id, Sport.TENNIS)
    result = final.result
    assert result is not None

    rating_stream = await store.load_stream(
        aggregate_type=RATING_AGGREGATE,
        aggregate_id=skill_rating_id(player_id, Sport.TENNIS),
    )
    initialised = rating_stream[0].event
    assert isinstance(initialised, RatingInitialised)
    assert initialised.mu == result.mu
    assert initialised.sigma == result.sigma
    assert initialised.band_name == result.band.name
    assert initialised.source_assessment_id == final.assessment_id


async def test_replaying_the_answer_that_finished_a_run_returns_its_result() -> None:
    # The replay branch is guarded on the question id alone, and a finished run
    # keeps its last-answered id, so a retry of the answer that ended the run
    # arrives here. It must describe the run the server actually holds — the
    # result — rather than reproduce a question for a run that has none.
    store = InMemoryEventStore()
    player_id = new_uuid()
    final, _ = await run_to_result(store, player_id)

    stream = await store.load_stream(
        aggregate_type=ASSESSMENT_AGGREGATE, aggregate_id=final.assessment_id
    )
    last_answer = [
        record.event for record in stream if isinstance(record.event, AnswerSubmitted)
    ][-1]

    store.appends = 0
    call = request(store)
    again = await call.submit.execute(
        SubmitAnswerCommand(
            player_id=player_id,
            assessment_id=final.assessment_id,
            question_id=last_answer.question_id,
            option_id=last_answer.option_id,
        )
    )

    assert again.status == "completed"
    assert again.question is None
    assert again.result is not None and final.result is not None
    assert again.result.mu == final.result.mu
    assert store.appends == 0
    assert call.uow.commits == 0


# --- The stop, recorded on the stream ------------------------------------------


async def _completion(
    store: InMemoryEventStore, assessment_id: UUID
) -> AssessmentCompleted:
    """The completion event as the store hands it back — encoded and decoded."""

    stream = await store.load_stream(
        aggregate_type=ASSESSMENT_AGGREGATE, aggregate_id=assessment_id
    )
    completed = stream[-1].event
    assert isinstance(completed, AssessmentCompleted)
    return completed


async def test_the_beginner_fast_path_records_that_it_is_why_the_run_stopped() -> None:
    # A run of one question is the shortest thing this engine produces, and
    # nothing about the transcript says whether that was the fast path or a
    # questionnaire that ran out of useful questions after one answer. The stop
    # is what distinguishes them, and it is the only place either is written.
    store = InMemoryEventStore()
    player_id = new_uuid()
    opening = (await start(store, player_id)).step
    assert opening.question is not None

    final = await request(store).submit.execute(
        SubmitAnswerCommand(
            player_id=player_id,
            assessment_id=opening.assessment_id,
            question_id=opening.question.id,
            option_id=NEVER_PLAYED_OPTION_ID,
        )
    )
    assert final.result is not None

    completed = await _completion(store, final.assessment_id)
    assert completed.stop_reason == STOP_BEGINNER
    assert completed.stop_value == 0.0


async def test_a_run_that_runs_out_of_useful_questions_records_the_gain() -> None:
    # The ordinary stop. The value is the marginal gain the best remaining
    # question offered, so it is asserted against the threshold that rejected it
    # rather than against a typed-in number — which is what makes the recorded
    # value usable for retuning that threshold against real runs.
    store = InMemoryEventStore()
    player_id = new_uuid()

    final, _ = await run_to_result(store, player_id, Sport.PADEL)

    completed = await _completion(store, final.assessment_id)
    assert completed.stop_reason == STOP_MARGINAL
    assert completed.stop_value is not None
    assert completed.stop_value < MIN_MARGINAL_GAIN


async def test_the_stop_is_readable_from_a_reloaded_assessment() -> None:
    # Through the repository, which is how a projection will reach it: the
    # aggregate carries the stop across replay rather than it being a fact only
    # the raw stream holds.
    store = InMemoryEventStore()
    player_id = new_uuid()
    final, _ = await run_to_result(store, player_id, Sport.TENNIS)

    reloaded = await request(store).repository.load(
        final.assessment_id, for_player=player_id
    )

    assert reloaded.is_completed
    assert reloaded.stop_reason == STOP_MARGINAL
    assert reloaded.stop_value is not None


# --- Revising: the transcript truncates, the stream does not ---------------------
#
# Submitting an answer for a question the run has already answered *changes* it,
# and discards every answer after it — each was pitched at a difficulty chosen
# from the estimate as it then stood (ADR-0020). What the use case owes on top of
# the aggregate is the routing: the engine is asked what the shortened transcript
# wants next, by the same code an ordinary answer runs.


async def _answered_run(
    store: InMemoryEventStore, player_id: UUID, answers: int
) -> AssessmentStep:
    """A run with ``answers`` questions answered, each with its last option."""

    step = (await start(store, player_id)).step
    for _ in range(answers):
        assert step.question is not None, "the run ended before it was long enough"
        step = await answer(store, player_id, step)
    return step


def _another_option(entry: TranscriptEntry) -> str:
    """An option that question offers which is not the one already recorded.

    Taken from the far end deliberately. Option 0 of the opening question is the
    beginner anchor, and revising to it ends the run — which is a behaviour worth
    a test of its own rather than an accident inside every other one.
    """

    return next(
        option.id
        for option in reversed(entry.question.options)
        if option.id != entry.option_id
    )


async def _revise(
    store: InMemoryEventStore,
    player_id: UUID,
    step: AssessmentStep,
    position: int,
    option_id: str | None = None,
) -> tuple[AssessmentStep, Request]:
    entry = step.transcript[position]
    call = request(store)
    revised = await call.submit.execute(
        SubmitAnswerCommand(
            player_id=player_id,
            assessment_id=step.assessment_id,
            question_id=entry.question.id,
            option_id=option_id or _another_option(entry),
        )
    )
    return revised, call


async def test_revising_truncates_and_asks_what_the_shorter_run_wants() -> None:
    store = InMemoryEventStore()
    player_id = new_uuid()
    step = await _answered_run(store, player_id, answers=3)
    first = step.transcript[0]

    revised, call = await _revise(store, player_id, step, position=0)

    # One answer left — the changed one — and the two that depended on it gone.
    assert revised.questions_asked == 1
    assert [entry.question.id for entry in revised.transcript] == [first.question.id]
    assert revised.transcript[0].option_id == _another_option(first)
    assert revised.question is not None
    assert [type(event) for event in call.events.published] == [
        AnswerRevised,
        QuestionAsked,
    ]
    assert call.uow.commits == 1


async def test_the_answers_it_discarded_are_still_on_the_stream() -> None:
    # The transcript shortened; the record did not. "A revision shortens the past;
    # it never edits it" is a claim about the stream, and a truncation that lost
    # the discarded answers would satisfy every transcript assertion above.
    store = InMemoryEventStore()
    player_id = new_uuid()
    step = await _answered_run(store, player_id, answers=3)
    asked_before = [entry.question.id for entry in step.transcript]

    await _revise(store, player_id, step, position=0)

    stream = await store.load_stream(
        aggregate_type=ASSESSMENT_AGGREGATE, aggregate_id=step.assessment_id
    )
    submitted = [
        event.question_id
        for event in (record.event for record in stream)
        if isinstance(event, AnswerSubmitted)
    ]
    assert submitted == asked_before
    assert any(isinstance(record.event, AnswerRevised) for record in stream)


async def test_re_selecting_the_option_already_recorded_records_nothing() -> None:
    store = InMemoryEventStore()
    player_id = new_uuid()
    step = await _answered_run(store, player_id, answers=3)
    entry = step.transcript[0]

    store.appends = 0
    unchanged, call = await _revise(
        store, player_id, step, position=0, option_id=entry.option_id
    )

    assert [e.question.id for e in unchanged.transcript] == [
        e.question.id for e in step.transcript
    ]
    assert unchanged.question is not None and step.question is not None
    assert unchanged.question.id == step.question.id
    assert store.appends == 0
    assert call.events.published == []
    assert call.uow.commits == 0


async def test_a_revision_can_stop_the_run() -> None:
    # The client must not have to predict this: ``never-played`` on the opening
    # question ends the questionnaire wherever it is submitted from, so a
    # revision reaches the completion path by exactly the route a last answer
    # does. Under ADR-0020 a stop is still what creates the rating; #59 is what
    # separates the two.
    store = InMemoryEventStore()
    player_id = new_uuid()
    step = await _answered_run(store, player_id, answers=3)

    final, call = await _revise(
        store, player_id, step, position=0, option_id=NEVER_PLAYED_OPTION_ID
    )

    assert final.question is None
    assert final.result is not None
    assert final.status == "completed"
    assert final.result.questions_asked == 1
    assert [type(event) for event in call.events.published] == [
        AnswerRevised,
        AssessmentCompleted,
        RatingInitialised,
    ]
    assert call.uow.commits == 1


async def test_revising_repeatedly_leaves_the_run_where_the_last_change_put_it() -> (
    None
):
    # Revising is not a one-step undo wearing another name: a run can be changed,
    # continued and changed again, and what the stream replays to is the last
    # word rather than a merge of the three.
    store = InMemoryEventStore()
    player_id = new_uuid()
    step = await _answered_run(store, player_id, answers=3)

    once, _ = await _revise(store, player_id, step, position=0)
    continued = await answer(store, player_id, once, option=0)
    twice, _ = await _revise(store, player_id, continued, position=0)

    assert [entry.question.id for entry in twice.transcript] == [
        step.transcript[0].question.id
    ]
    reloaded = await request(store).repository.load(
        step.assessment_id, for_player=player_id
    )
    assert [(entry.question_id, entry.option_id) for entry in reloaded.transcript] == [
        (entry.question.id, entry.option_id) for entry in twice.transcript
    ]


async def test_revising_once_the_rating_exists_is_refused() -> None:
    # The account of a player stops moving at the moment the platform starts
    # relying on it. Its own code, because the recovery is to show the rating
    # rather than to refetch a question that no longer exists.
    store = InMemoryEventStore()
    player_id = new_uuid()
    final, _ = await run_to_result(store, player_id)
    entry = final.transcript[0]

    call = request(store)
    with pytest.raises(AnswerNoLongerRevisable):
        await call.submit.execute(
            SubmitAnswerCommand(
                player_id=player_id,
                assessment_id=final.assessment_id,
                question_id=entry.question.id,
                option_id=_another_option(entry),
            )
        )

    assert call.events.published == []
    assert call.uow.commits == 0


async def test_an_abandoned_run_refuses_a_change_with_the_ordinary_conflict() -> None:
    # No rating to show, so there is nothing the not-revisable code would tell a
    # client that refetching does not: it reads the abandoned status and leaves.
    store = InMemoryEventStore()
    player_id = new_uuid()
    step = await _answered_run(store, player_id, answers=2)
    abandoning = request(store)
    run = await abandoning.repository.load(step.assessment_id, for_player=player_id)
    run.abandon(occurred_at=utc(2026, 8, 14))
    await abandoning.repository.save(run)

    entry = step.transcript[0]
    call = request(store)
    with pytest.raises(QuestionNotOutstanding):
        await call.submit.execute(
            SubmitAnswerCommand(
                player_id=player_id,
                assessment_id=step.assessment_id,
                question_id=entry.question.id,
                option_id=_another_option(entry),
            )
        )

    assert call.uow.commits == 0


async def test_an_option_the_revised_question_never_offered_is_rejected() -> None:
    store = InMemoryEventStore()
    player_id = new_uuid()
    step = await _answered_run(store, player_id, answers=2)

    call = request(store)
    with pytest.raises(InvalidAnswerOption):
        await call.submit.execute(
            SubmitAnswerCommand(
                player_id=player_id,
                assessment_id=step.assessment_id,
                question_id=step.transcript[0].question.id,
                option_id="not-an-option",
            )
        )

    assert call.events.published == []
    assert call.uow.commits == 0


async def test_two_devices_revising_at_once_fail_loudly() -> None:
    """A revision is an append with an expected version, exactly as an answer is.

    Over HTTP there is no seam to wedge the second writer into, which is why this
    is asserted here: the repository appends at the version the stream had when
    it was read, so a second writer that got there first must make the append
    refuse rather than interleave two accounts of one run.
    """

    store = InMemoryEventStore()
    player_id = new_uuid()
    step = await _answered_run(store, player_id, answers=3)
    entry = step.transcript[0]
    options = [
        option.id for option in entry.question.options if option.id != entry.option_id
    ]

    call = request(store)
    loaded = await call.repository.load(step.assessment_id, for_player=player_id)

    # The other device got there first, with a different change.
    stream = await store.load_stream(
        aggregate_type=ASSESSMENT_AGGREGATE, aggregate_id=step.assessment_id
    )
    concurrent = Assessment.from_history(record.event for record in stream)
    concurrent.revise(
        question_id=entry.question.id,
        option_id=options[0],
        occurred_at=utc(2026, 8, 14),
    )
    await store.append(
        aggregate_type=ASSESSMENT_AGGREGATE,
        aggregate_id=step.assessment_id,
        expected_version=len(stream),
        events=concurrent.pull_events(),
    )

    loaded.revise(
        question_id=entry.question.id,
        option_id=options[1],
        occurred_at=utc(2026, 8, 14),
    )
    with pytest.raises(EventStreamVersionConflict):
        await call.repository.save(loaded)
