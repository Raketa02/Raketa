"""``load_all_in_progress`` — the scan behind the entry gate's single read.

Two of its rules cannot be reached over HTTP, because ``POST /assessments`` is
idempotent per player and sport and will not open a second run for one sport. The
store can still hold one: the guard is a read before a write, so two starts that
both read before either commits each mint their own stream (recorded in
``create_assessment``'s docstring). These tests drive the scan directly, over a
stub store, so the collection's behaviour is pinned for a store that has one.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from app.application.events.store import StoredDomainEvent
from app.kernel import Sport
from app.modules.rating.application.find_in_progress_assessment import (
    load_all_in_progress,
    load_in_progress,
)
from app.modules.rating.domain.assessment import Assessment
from app.shared.domain import DomainEvent

NOW = datetime(2026, 8, 14, tzinfo=timezone.utc)
ENGINE = "racketskill-fusion-v3"


def _run(player_id: UUID, sport: Sport) -> Assessment:
    assessment = Assessment.start(
        assessment_id=uuid4(),
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


class StubEventStore:
    """Streams in the order they were opened, which is the order the store gives.

    Only the two read methods the scan uses are implemented; a write through this
    would be a test reaching past the seam it is testing.
    """

    def __init__(self, *assessments: Assessment) -> None:
        self._streams: dict[UUID, list[DomainEvent]] = {}
        self._opening: dict[UUID, dict[str, Any]] = {}
        for assessment in assessments:
            events = assessment.pull_events()
            self._streams[assessment.id] = events
            self._opening[assessment.id] = {
                "player_id": str(assessment.player_id),
                "sport": assessment.sport.value,
            }

    async def find_aggregate_ids_by_first_event(
        self, *, aggregate_type: str, payload_equals: Mapping[str, str]
    ) -> list[UUID]:
        assert aggregate_type == "assessment"
        return [
            stream_id
            for stream_id, opening in self._opening.items()
            if all(opening.get(key) == value for key, value in payload_equals.items())
        ]

    async def load_stream(
        self, *, aggregate_type: str, aggregate_id: UUID
    ) -> list[StoredDomainEvent]:
        return [
            StoredDomainEvent(
                id=uuid4(),
                aggregate_type=aggregate_type,
                aggregate_id=aggregate_id,
                version=version,
                event=event,
                occurred_at=NOW,
            )
            for version, event in enumerate(self._streams[aggregate_id], start=1)
        ]


async def test_two_open_runs_for_one_sport_yield_one_entry() -> None:
    # A stranded stream is not two sports. One entry per sport is what the entry
    # gate routes on, and a second entry would offer a run the resume read will
    # never hand back.
    player_id = uuid4()
    older = _run(player_id, Sport.PADEL)
    newer = _run(player_id, Sport.PADEL)
    store = StubEventStore(older, newer)

    entries = await load_all_in_progress(store, player_id=player_id)

    assert [a.id for a in entries] == [newer.id]


async def test_the_entry_is_the_run_the_per_sport_read_offers() -> None:
    # The two reads answer the same question about the same player. If they
    # disagreed about which run is open, the gate would route into one run and
    # the resume would load another, and no client could see the difference.
    player_id = uuid4()
    older = _run(player_id, Sport.PADEL)
    newer = _run(player_id, Sport.PADEL)
    store = StubEventStore(older, newer)

    collected = await load_all_in_progress(store, player_id=player_id)
    resumed = await load_in_progress(store, player_id=player_id, sport=Sport.PADEL)

    assert resumed is not None
    assert [a.id for a in collected] == [resumed.id]


async def test_a_sport_whose_only_open_run_is_the_older_one_still_appears() -> None:
    # Newest-first is a tie-break between open runs, not a stopping rule: a newer
    # run that has since ended must not hide the open one behind it.
    player_id = uuid4()
    open_run = _run(player_id, Sport.TENNIS)
    ended = _run(player_id, Sport.TENNIS)
    ended.abandon(occurred_at=NOW)
    store = StubEventStore(open_run, ended)

    entries = await load_all_in_progress(store, player_id=player_id)

    assert [a.id for a in entries] == [open_run.id]


async def test_entries_come_back_in_registry_order() -> None:
    player_id = uuid4()
    store = StubEventStore(
        _run(player_id, Sport.BADMINTON),
        _run(player_id, Sport.PADEL),
        _run(player_id, Sport.SQUASH),
    )

    entries = await load_all_in_progress(store, player_id=player_id)

    assert [a.sport for a in entries] == [Sport.PADEL, Sport.SQUASH, Sport.BADMINTON]
