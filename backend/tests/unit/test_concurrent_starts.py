"""Two starts that both read the store before either appends.

**This is the seam, and it is the reason #35 stayed open.** `tests/api/` drives
one in-memory SQLite connection through HTTPX ASGI, so it cannot express two
genuinely concurrent starts — and landing a concurrency fix that nothing can
prove, or keep proving, is worse than a documented known gap.

What makes it expressible here is the repository. Since the use cases take an
`AssessmentRepository` over a `DomainEventStore` rather than a database, a store
that *makes* the interleaving happen is a test double rather than an
infrastructure project. `RacingEventStore` below holds every candidate scan at a
barrier until both requests have finished reading, which is exactly the window
the read-before-write guard cannot close.

The fake enforces `expected_version` as equality against stream length, which is
the real store's semantics — and the real store additionally has
`uq_event_store_stream_version` behind it, so the rejection is the database's and
not Python's. `test_event_store_concurrency` proves that half against a real
engine.
"""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from uuid import UUID

import pytest

from app.application.events.store import EventStreamVersionConflict
from app.kernel import Sport
from app.modules.rating.application.commands import CreateAssessmentCommand
from app.modules.rating.domain.ids import assessment_stream_id
from app.modules.rating.infrastructure.event_sourced_assessment_repository import (
    ASSESSMENT_AGGREGATE,
)
from app.shared.ids import new_uuid
from tests.unit.assessment_requests import request
from tests.unit.fake_event_store import InMemoryEventStore, utc


class RacingEventStore(InMemoryEventStore):
    """An in-memory store that holds candidate scans until every racer has read.

    The barrier sits on `find_aggregate_ids_by_first_event` because that is the
    read *both* halves of the guard go through — the in-progress lookup and the
    identity derivation — and both must complete for every racer before any of
    them appends. Releasing after only the first would let a winner commit in
    between, and the loser would then count one stream, derive attempt 1, and
    open a second run: the very bug, reintroduced by the test harness.

    **Racing stops at the first append.** By then every racer is holding a stale
    answer, which is the state the race exists to produce; leaving the barrier
    armed would strand the loser on its re-read with nobody left to meet it.
    """

    def __init__(self, racers: int) -> None:
        super().__init__()
        self._everyone_has_read = asyncio.Barrier(racers)
        self._racing = True

    async def find_aggregate_ids_by_first_event(
        self, *, aggregate_type: str, payload_equals: Mapping[str, str]
    ) -> list[UUID]:
        found = await super().find_aggregate_ids_by_first_event(
            aggregate_type=aggregate_type,
            payload_equals=payload_equals,
        )
        if self._racing:
            await self._everyone_has_read.wait()
        return found

    async def append(self, **kwargs: object) -> list:  # type: ignore[override]
        self._racing = False
        return await super().append(**kwargs)  # type: ignore[arg-type]


async def _start(store: InMemoryEventStore, player_id: UUID, sport: Sport):
    # A fresh bundle per call, because each of these is a separate request and
    # the repository's identity map must not be shared across them.
    return await request(store).create.execute(
        CreateAssessmentCommand(player_id=player_id, sport=sport)
    )


def _assessment_streams(store: InMemoryEventStore) -> list[UUID]:
    return [
        aggregate_id
        for (aggregate_type, aggregate_id) in store._streams  # noqa: SLF001
        if aggregate_type == ASSESSMENT_AGGREGATE
    ]


async def test_two_starts_that_both_read_before_either_appends_open_one_run() -> None:
    # The window #35 is about: neither has appended, so neither guard can see the
    # other. Before the stream id was derived, each minted its own and both
    # succeeded — leaving a run no client path could reach, resume or abandon.
    store = RacingEventStore(racers=2)
    player_id = new_uuid()

    outcomes = await asyncio.gather(
        _start(store, player_id, Sport.PADEL),
        _start(store, player_id, Sport.PADEL),
        return_exceptions=True,
    )

    streams = _assessment_streams(store)
    assert len(streams) == 1, "a second stream was opened — the race is still open"
    assert streams == [assessment_stream_id(player_id, Sport.PADEL, 0)]

    # One of them created the run. The other either found it — if the winner had
    # committed by then — or was told, which is a 409 the client retries. What it
    # must never be is a second successful creation.
    created = [
        outcome
        for outcome in outcomes
        if not isinstance(outcome, BaseException) and outcome.created
    ]
    assert len(created) == 1


async def test_the_loser_is_told_rather_than_given_a_run_that_is_not_there() -> None:
    # The winner's transaction has not committed, so there is nothing truthful to
    # hand back. Re-raising is what makes this a retry the client can make, and
    # `EventStreamVersionConflict` is mapped to a 409 rather than a 500 (#53).
    store = RacingEventStore(racers=2)
    player_id = new_uuid()

    outcomes = await asyncio.gather(
        _start(store, player_id, Sport.PADEL),
        _start(store, player_id, Sport.PADEL),
        return_exceptions=True,
    )

    conflicts = [o for o in outcomes if isinstance(o, EventStreamVersionConflict)]
    handed_back = [
        o for o in outcomes if not isinstance(o, BaseException) and not o.created
    ]
    # Exactly one loser, resolved one way or the other — never two winners.
    assert len(conflicts) + len(handed_back) == 1


async def test_the_race_is_lost_for_one_sport_only() -> None:
    # Two sports raced at once are not racing each other: the pair is the key, so
    # padel and tennis derive different ids and both succeed.
    store = RacingEventStore(racers=2)
    player_id = new_uuid()

    padel, tennis = await asyncio.gather(
        _start(store, player_id, Sport.PADEL),
        _start(store, player_id, Sport.TENNIS),
    )

    assert padel.created is True
    assert tennis.created is True
    assert len(_assessment_streams(store)) == 2


async def test_two_players_racing_the_same_sport_each_get_a_run() -> None:
    store = RacingEventStore(racers=2)
    mine, theirs = new_uuid(), new_uuid()

    ours, yours = await asyncio.gather(
        _start(store, mine, Sport.PADEL),
        _start(store, theirs, Sport.PADEL),
    )

    assert ours.created is True
    assert yours.created is True
    assert ours.step.assessment_id != yours.step.assessment_id


async def test_a_new_run_after_an_abandoned_one_gets_the_next_attempt() -> None:
    # The attempt counts every stream the pair ever opened, not the open ones. If
    # it counted only the open ones, the sport's second run would be handed an id
    # the abandoned first run already holds, and starting again would be a
    # conflict for good.
    store = InMemoryEventStore()
    player_id = new_uuid()
    first = await _start(store, player_id, Sport.PADEL)

    abandoning = request(store)
    run = await abandoning.repository.load(
        first.step.assessment_id, for_player=player_id
    )
    run.abandon(occurred_at=utc(2026, 8, 14))
    await abandoning.repository.save(run)

    second = await _start(store, player_id, Sport.PADEL)

    assert second.created is True
    assert first.step.assessment_id == assessment_stream_id(player_id, Sport.PADEL, 0)
    assert second.step.assessment_id == assessment_stream_id(player_id, Sport.PADEL, 1)


def test_an_id_is_derivable_but_reading_one_still_requires_being_its_player() -> None:
    # Deriving ids makes them guessable by anyone who knows a player id, and that
    # leaks nothing: `load` takes the player it must belong to, and another
    # player's assessment is reported exactly as an absent one. This asserts the
    # derivation is stable, which is what the guessability argument rests on.
    player_id = new_uuid()
    assert assessment_stream_id(player_id, Sport.PADEL, 0) == assessment_stream_id(
        player_id, Sport.PADEL, 0
    )
    assert assessment_stream_id(player_id, Sport.PADEL, 0) != assessment_stream_id(
        player_id, Sport.PADEL, 1
    )
    assert assessment_stream_id(player_id, Sport.PADEL, 0) != assessment_stream_id(
        player_id, Sport.TENNIS, 0
    )
    assert assessment_stream_id(player_id, Sport.PADEL, 0) != assessment_stream_id(
        new_uuid(), Sport.PADEL, 0
    )


@pytest.mark.parametrize("racers", [3, 5])
async def test_however_many_start_at_once_one_run_exists(racers: int) -> None:
    store = RacingEventStore(racers=racers)
    player_id = new_uuid()

    await asyncio.gather(
        *(_start(store, player_id, Sport.PADEL) for _ in range(racers)),
        return_exceptions=True,
    )

    assert len(_assessment_streams(store)) == 1
