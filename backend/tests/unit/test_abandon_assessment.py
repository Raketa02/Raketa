"""Abandoning a run, and the repository underneath it.

These are the first use-case unit tests in the rating context. Until the
repository existed, exercising one meant standing up an event store, a unit of
work and a publisher together, so behaviour worth a handful of cheap tests —
idempotent abandonment, the ownership guard, the transaction boundary — was
reachable only through HTTP over SQLite.

The event store is faked; the repository is not. The identity map, the version
arithmetic and the encoded stream keys are what this slice introduced, and a
repository fake would leave every one of them exercised by nothing.
"""

from __future__ import annotations

import pytest

from app.application.events.store import EventStreamVersionConflict
from app.kernel import Sport
from app.modules.rating.application.abandon_assessment import AbandonAssessment
from app.modules.rating.application.commands import AbandonAssessmentCommand
from app.modules.rating.domain.assessment import Assessment, AssessmentStatus
from app.modules.rating.domain.errors import AssessmentNotFound
from app.modules.rating.domain.events import AssessmentAbandoned
from app.modules.rating.infrastructure.event_sourced_assessment_repository import (
    ASSESSMENT_AGGREGATE,
    EventSourcedAssessmentRepository,
)
from app.shared.ids import new_uuid
from tests.unit.fake_event_store import (
    CountingUnitOfWork,
    FrozenClock,
    InMemoryEventStore,
    RecordingPublisher,
    utc,
)

NOW = utc(2026, 8, 14)
ENGINE = "racketskill-fusion-v3"


def _started(player_id, sport: Sport = Sport.PADEL) -> Assessment:
    assessment = Assessment.start(
        assessment_id=new_uuid(),
        player_id=player_id,
        sport=sport,
        engine_version=ENGINE,
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


async def _seed(store: InMemoryEventStore, assessment: Assessment) -> Assessment:
    """Put a run in the store as a previous request would have left it."""

    await store.append(
        aggregate_type=ASSESSMENT_AGGREGATE,
        aggregate_id=assessment.id,
        expected_version=0,
        events=assessment.pull_events(),
    )
    return assessment


def _build(store: InMemoryEventStore):
    events = RecordingPublisher()
    uow = CountingUnitOfWork()
    repository = EventSourcedAssessmentRepository(event_store=store, events=events)
    use_case = AbandonAssessment(assessments=repository, uow=uow, clock=FrozenClock())
    return use_case, repository, events, uow


# --- abandoning ----------------------------------------------------------


async def test_abandoning_records_the_end_of_the_run() -> None:
    store = InMemoryEventStore()
    player_id = new_uuid()
    run = await _seed(store, _started(player_id))
    use_case, _, events, uow = _build(store)

    await use_case.execute(
        AbandonAssessmentCommand(player_id=player_id, assessment_id=run.id)
    )

    stored = await store.load_stream(
        aggregate_type=ASSESSMENT_AGGREGATE, aggregate_id=run.id
    )
    assert isinstance(stored[-1].event, AssessmentAbandoned)
    # Published for the outbox, and committed exactly once.
    assert [type(event) for event in events.published] == [AssessmentAbandoned]
    assert uow.commits == 1

    replayed = Assessment.from_history(record.event for record in stored)
    assert replayed.status is AssessmentStatus.ABANDONED


async def test_abandoning_twice_writes_nothing_the_second_time() -> None:
    # The retry succeeds. The no-op is the repository's — the aggregate records
    # nothing, so ``save`` has nothing to append — and the use case never asks.
    store = InMemoryEventStore()
    player_id = new_uuid()
    run = await _seed(store, _started(player_id))
    command = AbandonAssessmentCommand(player_id=player_id, assessment_id=run.id)

    first, _, _, _ = _build(store)
    await first.execute(command)
    after_first = len(
        await store.load_stream(
            aggregate_type=ASSESSMENT_AGGREGATE, aggregate_id=run.id
        )
    )

    second, _, events, _ = _build(store)
    store.appends = 0
    await second.execute(command)

    stored = await store.load_stream(
        aggregate_type=ASSESSMENT_AGGREGATE, aggregate_id=run.id
    )
    assert len(stored) == after_first
    assert events.published == []
    # Not merely "wrote nothing": the store was never asked to write.
    assert store.appends == 0


async def test_another_players_assessment_is_not_found() -> None:
    store = InMemoryEventStore()
    run = await _seed(store, _started(new_uuid()))
    use_case, _, _, uow = _build(store)

    with pytest.raises(AssessmentNotFound):
        await use_case.execute(
            AbandonAssessmentCommand(player_id=new_uuid(), assessment_id=run.id)
        )

    # Indistinguishable from absent, and nothing was written or committed.
    assert uow.commits == 0
    stored = await store.load_stream(
        aggregate_type=ASSESSMENT_AGGREGATE, aggregate_id=run.id
    )
    assert not any(isinstance(record.event, AssessmentAbandoned) for record in stored)


async def test_an_absent_assessment_is_not_found() -> None:
    store = InMemoryEventStore()
    use_case, _, _, uow = _build(store)

    with pytest.raises(AssessmentNotFound):
        await use_case.execute(
            AbandonAssessmentCommand(
                player_id=new_uuid(), assessment_id=new_uuid()
            )
        )

    assert uow.commits == 0


async def test_a_concurrent_write_since_the_load_is_a_version_conflict() -> None:
    """Reproducible for the first time, because the version is now recoverable.

    The repository appends at the version the stream had when it was read. A
    second writer that got there first moves the stream past it, and the append
    must refuse rather than interleave. Over HTTP there is no seam to wedge the
    second writer into, which is why this had no test before.
    """

    store = InMemoryEventStore()
    player_id = new_uuid()
    run = await _seed(store, _started(player_id))
    _, repository, _, _ = _build(store)

    loaded = await repository.load(run.id, for_player=player_id)

    # Somebody else answered the outstanding question in between.
    concurrent = Assessment.from_history(
        record.event
        for record in await store.load_stream(
            aggregate_type=ASSESSMENT_AGGREGATE, aggregate_id=run.id
        )
    )
    concurrent.answer(
        question_id="opening.regularity", option_id="weekly", occurred_at=NOW
    )
    await store.append(
        aggregate_type=ASSESSMENT_AGGREGATE,
        aggregate_id=run.id,
        expected_version=2,
        events=concurrent.pull_events(),
    )

    loaded.abandon(occurred_at=NOW)
    with pytest.raises(EventStreamVersionConflict):
        await repository.save(loaded)


# --- the repository's own bookkeeping ------------------------------------


async def test_an_aggregate_never_loaded_is_appended_at_version_zero() -> None:
    # "This stream does not exist yet" follows from never having read it, so no
    # caller has to say so — and no caller can say so wrongly.
    store = InMemoryEventStore()
    _, repository, events, _ = _build(store)
    fresh = _started(new_uuid())

    await repository.save(fresh)

    stored = await store.load_stream(
        aggregate_type=ASSESSMENT_AGGREGATE, aggregate_id=fresh.id
    )
    assert [record.version for record in stored] == [1, 2]
    assert len(events.published) == 2


async def test_saving_twice_in_one_request_uses_the_version_the_first_save_left(
) -> None:
    # The identity map is updated after every append, not only on load, so a use
    # case that saves the same aggregate twice does not collide with itself.
    store = InMemoryEventStore()
    _, repository, _, _ = _build(store)
    fresh = _started(new_uuid())

    await repository.save(fresh)
    fresh.abandon(occurred_at=NOW)
    await repository.save(fresh)

    stored = await store.load_stream(
        aggregate_type=ASSESSMENT_AGGREGATE, aggregate_id=fresh.id
    )
    assert [record.version for record in stored] == [1, 2, 3]


async def test_saving_an_aggregate_with_nothing_pending_publishes_nothing() -> None:
    store = InMemoryEventStore()
    player_id = new_uuid()
    run = await _seed(store, _started(player_id))
    _, repository, events, _ = _build(store)

    loaded = await repository.load(run.id, for_player=player_id)
    await repository.save(loaded)

    assert events.published == []
    stored = await store.load_stream(
        aggregate_type=ASSESSMENT_AGGREGATE, aggregate_id=run.id
    )
    assert len(stored) == 2


async def test_the_repository_finds_the_open_run_it_keyed_on_the_stored_payload(
) -> None:
    # The finders match the *stored JSON* of a stream's opening event. Running
    # the real codec in the double is what makes this test able to fail: a
    # renamed field returns nothing, which reads exactly like "no run open".
    store = InMemoryEventStore()
    player_id = new_uuid()
    padel = await _seed(store, _started(player_id, Sport.PADEL))
    await _seed(store, _started(new_uuid(), Sport.PADEL))
    _, repository, _, _ = _build(store)

    found = await repository.find_open(player_id=player_id, sport=Sport.PADEL)
    assert found is not None and found.id == padel.id

    assert await repository.find_open(player_id=player_id, sport=Sport.TENNIS) is None
    assert [run.id for run in await repository.find_all_open(player_id=player_id)] == [
        padel.id
    ]
