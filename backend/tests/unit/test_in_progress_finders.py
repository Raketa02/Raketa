"""The repository's finders — the scan behind resume and the entry gate.

Two of the rules pinned here cannot be reached over HTTP, because
``POST /assessments`` is idempotent per player and sport and will not open a
second run for one sport. The store can still hold one: the guard is a read
before a write, so two starts that both read before either commits each mint
their own stream (recorded in ``create_assessment``'s docstring). These tests
seed the store directly, so the finders' behaviour is pinned for a store that
has one.

They go through the repository rather than past it. The finders match the
*stored JSON payload* of a stream's opening event, and running the real codec in
the double is what makes a renamed field fail here: the query would simply
return nothing, which reads exactly like "no run in progress".
"""

from __future__ import annotations

from app.kernel import Sport
from app.modules.rating.domain.assessment import Assessment
from app.modules.rating.infrastructure.event_sourced_assessment_repository import (
    ASSESSMENT_AGGREGATE,
    EventSourcedAssessmentRepository,
)
from app.shared.ids import new_uuid
from tests.unit.fake_event_store import (
    InMemoryEventStore,
    RecordingPublisher,
    utc,
)

NOW = utc(2026, 8, 14)
ENGINE = "racketskill-fusion-v3"


def _started(player_id, sport: Sport) -> Assessment:
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


def _repository(store: InMemoryEventStore) -> EventSourcedAssessmentRepository:
    return EventSourcedAssessmentRepository(
        event_store=store, events=RecordingPublisher()
    )


async def test_two_open_runs_for_one_sport_yield_one_entry() -> None:
    # A stranded stream is not two sports. One entry per sport is what the entry
    # gate routes on, and a second entry would offer a run the resume read will
    # never hand back.
    store = InMemoryEventStore()
    player_id = new_uuid()
    await _seed(store, _started(player_id, Sport.PADEL))
    newer = await _seed(store, _started(player_id, Sport.PADEL))

    entries = await _repository(store).find_all_open(player_id=player_id)

    assert [run.id for run in entries] == [newer.id]


async def test_the_entry_is_the_run_the_per_sport_read_offers() -> None:
    # The two finders answer the same question about the same player. If they
    # disagreed about which run is open, the gate would route into one run and
    # the resume would load another, and no client could see the difference.
    # They share one scan, so the agreement is structural — this is what says so.
    store = InMemoryEventStore()
    player_id = new_uuid()
    await _seed(store, _started(player_id, Sport.PADEL))
    await _seed(store, _started(player_id, Sport.PADEL))
    repository = _repository(store)

    collected = await repository.find_all_open(player_id=player_id)
    resumed = await repository.find_open(player_id=player_id, sport=Sport.PADEL)

    assert resumed is not None
    assert [run.id for run in collected] == [resumed.id]


async def test_a_sport_whose_only_open_run_is_the_older_one_still_appears() -> None:
    # Newest-first is a tie-break between open runs, not a stopping rule: a newer
    # run that has since ended must not hide the open one behind it.
    store = InMemoryEventStore()
    player_id = new_uuid()
    open_run = await _seed(store, _started(player_id, Sport.TENNIS))
    ended = _started(player_id, Sport.TENNIS)
    ended.abandon(occurred_at=NOW)
    await _seed(store, ended)
    repository = _repository(store)

    assert [run.id for run in await repository.find_all_open(player_id=player_id)] == [
        open_run.id
    ]
    found = await repository.find_open(player_id=player_id, sport=Sport.TENNIS)
    assert found is not None and found.id == open_run.id


async def test_entries_come_back_in_registry_order() -> None:
    store = InMemoryEventStore()
    player_id = new_uuid()
    await _seed(store, _started(player_id, Sport.BADMINTON))
    await _seed(store, _started(player_id, Sport.PADEL))
    await _seed(store, _started(player_id, Sport.SQUASH))

    entries = await _repository(store).find_all_open(player_id=player_id)

    assert [run.sport for run in entries] == [
        Sport.PADEL,
        Sport.SQUASH,
        Sport.BADMINTON,
    ]


async def test_another_players_open_run_is_not_this_players() -> None:
    store = InMemoryEventStore()
    player_id = new_uuid()
    await _seed(store, _started(new_uuid(), Sport.PADEL))

    assert await _repository(store).find_all_open(player_id=player_id) == []


async def test_a_found_run_can_be_saved_at_the_version_it_was_found_at() -> None:
    # The finders register what they load in the identity map, so a run that was
    # found is a run that can be acted on. Without that, saving one would append
    # at version zero and collide with its own stream.
    store = InMemoryEventStore()
    player_id = new_uuid()
    run = await _seed(store, _started(player_id, Sport.PADEL))
    repository = _repository(store)

    found = await repository.find_open(player_id=player_id, sport=Sport.PADEL)
    assert found is not None
    found.abandon(occurred_at=NOW)
    await repository.save(found)

    stored = await store.load_stream(
        aggregate_type=ASSESSMENT_AGGREGATE, aggregate_id=run.id
    )
    assert [record.version for record in stored] == [1, 2, 3]
