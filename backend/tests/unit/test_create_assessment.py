"""Starting a run, and the idempotence that keeps a double tap harmless.

The guard is scoped to runs that are *in progress*, never to any run that ever
existed, so a sport whose previous run ended still starts a genuinely new one.
Both halves are cheap here and were reachable only through HTTP before.
"""

from __future__ import annotations

from app.kernel import Sport
from app.modules.rating.application.commands import CreateAssessmentCommand
from app.modules.rating.domain.assessment import Assessment
from app.modules.rating.domain.events import AssessmentStarted, QuestionAsked
from app.modules.rating.infrastructure.event_sourced_assessment_repository import (
    ASSESSMENT_AGGREGATE,
)
from app.shared.ids import new_uuid
from tests.unit.assessment_requests import request, start
from tests.unit.fake_event_store import InMemoryEventStore, utc

NOW = utc(2026, 8, 14)


async def _stream(store: InMemoryEventStore, assessment_id):
    return await store.load_stream(
        aggregate_type=ASSESSMENT_AGGREGATE, aggregate_id=assessment_id
    )


async def test_starting_records_the_run_and_its_opening_question() -> None:
    store = InMemoryEventStore()
    player_id = new_uuid()
    call = request(store)

    started = await call.create.execute(
        CreateAssessmentCommand(player_id=player_id, sport=Sport.PADEL)
    )

    assert started.created is True
    assert started.step.question is not None
    assert started.step.question.id == "opening.regularity"
    # Nothing is answered yet, and the opening question does not count itself.
    assert started.step.questions_asked == 0

    stored = await _stream(store, started.step.assessment_id)
    assert [type(record.event) for record in stored] == [
        AssessmentStarted,
        QuestionAsked,
    ]
    assert [record.version for record in stored] == [1, 2]
    assert len(call.events.published) == 2
    assert call.uow.commits == 1


async def test_starting_again_hands_back_the_open_run_and_writes_nothing() -> None:
    # The retry after a lost response, the second device, the double tap slower
    # than a round trip: all the same call, and none of them opens a second
    # stream or costs a transaction.
    store = InMemoryEventStore()
    player_id = new_uuid()
    first = await start(store, player_id)

    store.appends = 0
    again = request(store)
    second = await again.create.execute(
        CreateAssessmentCommand(player_id=player_id, sport=Sport.PADEL)
    )

    assert second.created is False
    assert second.step.assessment_id == first.step.assessment_id
    assert second.step.question is not None
    assert second.step.question.id == first.step.question.id
    # Not merely "wrote nothing": the store was never asked, and nothing committed.
    assert store.appends == 0
    assert again.events.published == []
    assert again.uow.commits == 0


async def test_another_sport_is_another_run() -> None:
    # Every sport is fully isolated: an open padel run says nothing about tennis.
    store = InMemoryEventStore()
    player_id = new_uuid()
    padel = await start(store, player_id, Sport.PADEL)

    tennis = await start(store, player_id, Sport.TENNIS)

    assert tennis.created is True
    assert tennis.step.assessment_id != padel.step.assessment_id


async def test_a_sport_whose_run_ended_starts_a_new_one() -> None:
    # The guard asks whether a run is *in progress*, not whether one ever
    # existed — otherwise abandoning would lock the sport out for good.
    store = InMemoryEventStore()
    player_id = new_uuid()
    first = await start(store, player_id)

    abandoning = request(store)
    run = await abandoning.repository.load(
        first.step.assessment_id, for_player=player_id
    )
    run.abandon(occurred_at=NOW)
    await abandoning.repository.save(run)

    second = await start(store, player_id)

    assert second.created is True
    assert second.step.assessment_id != first.step.assessment_id
    replayed = Assessment.from_history(
        record.event for record in await _stream(store, second.step.assessment_id)
    )
    assert replayed.is_in_progress
