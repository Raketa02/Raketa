"""Starting a run: the idempotence that keeps a double tap harmless, and the
one sport that cannot be started at all.

The in-progress guard is scoped to runs that are *in progress*, never to any run
that ever existed, so a sport whose previous run was abandoned still starts a
genuinely new one. A sport the player is already **rated** at is a different
answer — refused outright, because its rating stream can hold only one opening
event and the store would otherwise say so on the last answer (#53).

Both halves are cheap here and were reachable only through HTTP before.
"""

from __future__ import annotations

from uuid import UUID

import pytest

from app.kernel import Sport
from app.modules.rating.application.commands import CreateAssessmentCommand
from app.modules.rating.domain.assessment import Assessment
from app.modules.rating.domain.errors import SportAlreadyRated
from app.modules.rating.domain.events import AssessmentStarted, QuestionAsked
from app.modules.rating.infrastructure.event_sourced_assessment_repository import (
    ASSESSMENT_AGGREGATE,
)
from app.shared.ids import new_uuid
from tests.unit.assessment_requests import request, run_to_result, start
from tests.unit.fake_event_store import InMemoryEventStore, utc

NOW = utc(2026, 8, 14)


async def _stream(store: InMemoryEventStore, assessment_id):
    return await store.load_stream(
        aggregate_type=ASSESSMENT_AGGREGATE, aggregate_id=assessment_id
    )


async def _strand_an_open_run(
    store: InMemoryEventStore, player_id: UUID, sport: Sport
) -> UUID:
    """An open run on a sport that is already rated — a state the API can no
    longer produce, and which a store written before the guard can hold.

    Built through the aggregate and the repository rather than by starting one,
    because starting one is precisely what is now refused.
    """

    bundle = request(store)
    run = Assessment.start(
        assessment_id=new_uuid(),
        player_id=player_id,
        sport=sport,
        engine_version="test",
        occurred_at=NOW,
    )
    await bundle.repository.save(run)
    return run.id


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


async def test_a_rated_sport_is_refused_before_a_question_is_asked() -> None:
    # #53, at the cheap end. Completing a second run for a sport appends a
    # second opening event to a rating stream keyed by (player, sport), and the
    # store rejects it — which the player used to discover on the *last* answer
    # of a whole questionnaire.
    store = InMemoryEventStore()
    player_id = new_uuid()
    await run_to_result(store, player_id, Sport.PADEL)

    store.appends = 0
    refusing = request(store)
    with pytest.raises(SportAlreadyRated):
        await refusing.create.execute(
            CreateAssessmentCommand(player_id=player_id, sport=Sport.PADEL)
        )

    # Refused, not rolled back: no stream opened, nothing published, no commit.
    assert store.appends == 0
    assert refusing.events.published == []
    assert refusing.uow.commits == 0


async def test_rating_one_sport_leaves_the_others_startable() -> None:
    # The refusal is keyed by the pair, not by the player. This is the assertion
    # that fails if the existence check ever loses its sport.
    store = InMemoryEventStore()
    player_id = new_uuid()
    await run_to_result(store, player_id, Sport.PADEL)

    tennis = await start(store, player_id, Sport.TENNIS)

    assert tennis.created is True


async def test_another_players_rating_does_not_refuse_this_player() -> None:
    store = InMemoryEventStore()
    mine, theirs = new_uuid(), new_uuid()
    await run_to_result(store, theirs, Sport.PADEL)

    started = await start(store, mine, Sport.PADEL)

    assert started.created is True


async def test_the_refusal_precedes_the_in_progress_lookup() -> None:
    # Ordering, asserted rather than assumed. A run left open on a sport that
    # was later rated cannot arise from the shipped flow, but it can exist in a
    # store written before this guard did — and handing it back would only move
    # the failure to the answer that would have finished it.
    store = InMemoryEventStore()
    player_id = new_uuid()
    await run_to_result(store, player_id, Sport.PADEL)
    stranded = await _strand_an_open_run(store, player_id, Sport.PADEL)

    with pytest.raises(SportAlreadyRated):
        await request(store).create.execute(
            CreateAssessmentCommand(player_id=player_id, sport=Sport.PADEL)
        )

    # The stranded run is untouched and still abandonable through its own route.
    replayed = Assessment.from_history(
        record.event for record in await _stream(store, stranded)
    )
    assert replayed.is_in_progress
