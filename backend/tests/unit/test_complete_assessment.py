"""Completing a stopped assessment — the one call that creates a Skill rating.

Stopping and completing are two moments (ADR-0020). Answering the question the
engine has heard enough after records an answer and nothing else; the rating
comes into existence here, on a request of its own, which is what lets a review
of every answer sit between the two.

Most of this file used to live in ``test_submit_answer.py``, because a last
answer was what completed a run. It is the same set of facts — one transaction
for two aggregates, the outbox order, the recorded stop — asserted against the
call that now performs them.
"""

from __future__ import annotations

from uuid import UUID

import pytest

from app.engines.racketskill.v3.engine import (
    MIN_MARGINAL_GAIN,
    STOP_BEGINNER,
    STOP_MARGINAL,
)
from app.engines.racketskill.v3.questions import NEVER_PLAYED_OPTION_ID
from app.kernel import Sport
from app.modules.rating.application.commands import (
    CompleteAssessmentCommand,
    SubmitAnswerCommand,
)
from app.modules.rating.domain.errors import (
    AssessmentNotFound,
    AssessmentNotStopped,
)
from app.modules.rating.domain.events import (
    AnswerSubmitted,
    AssessmentCompleted,
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
    request,
    run_to_result,
    run_to_stop,
    start,
)
from tests.unit.fake_event_store import InMemoryEventStore, utc


async def _complete(store: InMemoryEventStore, player_id: UUID, assessment_id: UUID):
    call = request(store)
    step = await call.complete.execute(
        CompleteAssessmentCommand(player_id=player_id, assessment_id=assessment_id)
    )
    return step, call


# --- The stop creates nothing ---------------------------------------------------


async def test_the_answer_that_stops_the_questionnaire_creates_no_rating() -> None:
    store = InMemoryEventStore()
    player_id = new_uuid()

    stopped, answering = await run_to_stop(store, player_id, Sport.PADEL)

    # Neither a question nor a result, and still in progress: the run has
    # stopped asking and nothing has been rated.
    assert stopped.question is None
    assert stopped.result is None
    assert stopped.status == "in_progress"
    assert stopped.transcript, "the answers are served for the review to draw"

    # The last answer recorded an answer and nothing else.
    assert [type(event) for event in answering.events.published] == [AnswerSubmitted]
    assert (
        await store.load_stream(
            aggregate_type=RATING_AGGREGATE,
            aggregate_id=skill_rating_id(player_id, Sport.PADEL),
        )
        == []
    )


async def test_the_beginner_stops_after_one_answer_rather_than_being_rated() -> None:
    # The shortest run there is, and the one whose single answer carries the most
    # weight. It reaches the same stop as everybody else, so the review is one
    # rule rather than one rule and an exception.
    store = InMemoryEventStore()
    player_id = new_uuid()
    opening = (await start(store, player_id)).step
    assert opening.question is not None

    stopped = await request(store).submit.execute(
        SubmitAnswerCommand(
            player_id=player_id,
            assessment_id=opening.assessment_id,
            question_id=opening.question.id,
            option_id=NEVER_PLAYED_OPTION_ID,
        )
    )

    assert stopped.question is None and stopped.result is None
    assert stopped.status == "in_progress"
    assert stopped.questions_asked == 1


# --- Completion: one transaction, two streams -----------------------------------


async def test_completing_writes_both_streams_in_one_transaction() -> None:
    store = InMemoryEventStore()
    player_id = new_uuid()

    final, completing = await run_to_result(store, player_id, Sport.PADEL)

    assert final.question is None and final.result is not None
    assert final.status == "completed"

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
    # outbox before the rating's — the order they happened in. The answer is not
    # among them: it was a different request, several screens ago.
    assert completing.uow.commits == 1
    assert [type(event) for event in completing.events.published] == [
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


async def test_the_result_is_the_one_the_stopped_transcript_always_implied() -> None:
    # The rating is a pure function of the transcript, and the transcript did not
    # move between the stop and the completion. So the delay a review screen
    # introduces cannot change what a player is rated.
    store = InMemoryEventStore()
    player_id = new_uuid()
    stopped, _ = await run_to_stop(store, player_id, Sport.SQUASH)

    final, _ = await _complete(store, player_id, stopped.assessment_id)

    assert final.result is not None
    assert final.questions_asked == stopped.questions_asked
    assert final.result.questions_asked == stopped.questions_asked
    assert final.transcript == stopped.transcript


# --- Completing twice, and the two refusals --------------------------------------


async def test_completing_twice_records_nothing_and_returns_the_same_result() -> None:
    # The control a player double-taps on a slow connection. A conflict here is
    # one the client would have to translate back into "you already have your
    # rating", so this does it instead.
    store = InMemoryEventStore()
    player_id = new_uuid()
    stopped, _ = await run_to_stop(store, player_id)
    first, _ = await _complete(store, player_id, stopped.assessment_id)

    store.appends = 0
    again, call = await _complete(store, player_id, stopped.assessment_id)

    assert again.status == "completed"
    assert again.result == first.result
    assert store.appends == 0
    assert call.events.published == []
    assert call.uow.commits == 0


async def test_completing_a_run_that_is_still_asking_is_refused() -> None:
    store = InMemoryEventStore()
    player_id = new_uuid()
    opening = (await start(store, player_id)).step

    call = request(store)
    with pytest.raises(AssessmentNotStopped):
        await call.complete.execute(
            CompleteAssessmentCommand(
                player_id=player_id, assessment_id=opening.assessment_id
            )
        )

    assert call.events.published == []
    assert call.uow.commits == 0


async def test_completing_an_abandoned_run_is_refused() -> None:
    # It never stopped — it stopped being. There is no rating to hand back and
    # the recovery is the same as for a run still asking: refetch and render.
    store = InMemoryEventStore()
    player_id = new_uuid()
    stopped, _ = await run_to_stop(store, player_id)

    abandoning = request(store)
    assessment = await abandoning.repository.load(
        stopped.assessment_id, for_player=player_id
    )
    assessment.abandon(occurred_at=utc(2026, 8, 15))
    await abandoning.repository.save(assessment)
    await abandoning.uow.commit()

    call = request(store)
    with pytest.raises(AssessmentNotStopped):
        await call.complete.execute(
            CompleteAssessmentCommand(
                player_id=player_id, assessment_id=stopped.assessment_id
            )
        )

    assert call.uow.commits == 0


async def test_another_players_assessment_cannot_be_completed() -> None:
    store = InMemoryEventStore()
    player_id = new_uuid()
    stopped, _ = await run_to_stop(store, player_id)

    call = request(store)
    with pytest.raises(AssessmentNotFound):
        await call.complete.execute(
            CompleteAssessmentCommand(
                player_id=new_uuid(), assessment_id=stopped.assessment_id
            )
        )

    assert call.uow.commits == 0


# --- The stop, recorded on the stream -------------------------------------------
#
# Nothing serves it, and that is deliberate: a decision never recorded cannot be
# recovered later. It is re-derived at completion time by asking the engine what
# the transcript does — the same determinism the outstanding question and the
# served transcript rest on — rather than carried from the answer that reached it.


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

    stopped = await request(store).submit.execute(
        SubmitAnswerCommand(
            player_id=player_id,
            assessment_id=opening.assessment_id,
            question_id=opening.question.id,
            option_id=NEVER_PLAYED_OPTION_ID,
        )
    )
    final, _ = await _complete(store, player_id, stopped.assessment_id)
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
