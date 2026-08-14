"""Answering, and the four ways an answer can be refused or ignored.

Idempotency comes from the domain, not a header: an answer is accepted only for
the question currently outstanding, re-submitting the just-answered one records
nothing, and anything else conflicts. Completion writes two streams in one
transaction, which is the assertion this file exists for — it was reachable only
through HTTP over SQLite before the repository.
"""

from __future__ import annotations

import pytest

from app.kernel import Sport
from app.modules.rating.application.commands import SubmitAnswerCommand
from app.modules.rating.domain.errors import (
    AssessmentNotFound,
    InvalidAnswerOption,
    QuestionNotOutstanding,
)
from app.modules.rating.domain.events import (
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
from tests.unit.assessment_requests import answer, request, run_to_result, start
from tests.unit.fake_event_store import InMemoryEventStore


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
    store = InMemoryEventStore()
    player_id = new_uuid()
    final, _ = await run_to_result(store, player_id)

    call = request(store)
    with pytest.raises(QuestionNotOutstanding):
        await call.submit.execute(
            SubmitAnswerCommand(
                player_id=player_id,
                assessment_id=final.assessment_id,
                question_id="opening.regularity",
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
