from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

import pytest

from app.shared.clock import Clock
from app.shared.events import (
    DispatchResult,
    EventRecorder,
    EventRegistry,
    InProcessEventBus,
    OutboxRecord,
    OutboxRelay,
)


@dataclass(frozen=True)
class _SampleEvent:
    aggregate_id: UUID
    label: str
    occurred_at: datetime


def test_event_recorder_drains_then_resets():
    recorder = EventRecorder()
    event = _SampleEvent(
        aggregate_id=UUID(int=1), label="x", occurred_at=datetime.now(timezone.utc)
    )
    recorder.record(event)
    assert recorder.pull() == [event]
    assert recorder.pull() == []


def test_event_registry_roundtrip_uuid_and_datetime():
    registry = EventRegistry()
    registry.register(_SampleEvent)
    original = _SampleEvent(
        aggregate_id=UUID(int=42),
        label="hello",
        occurred_at=datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc),
    )

    name = registry.name_for(type(original))
    payload = registry.serialize(original)
    restored = registry.deserialize(name, payload)

    assert restored == original


def test_event_registry_rejects_unknown_class_on_lookup():
    registry = EventRegistry()
    with pytest.raises(LookupError):
        registry.name_for(_SampleEvent)


def test_event_registry_rejects_duplicate_registration_with_different_class():
    registry = EventRegistry()
    registry.register(_SampleEvent)

    @dataclass(frozen=True)
    class _ShadowEvent:
        occurred_at: datetime

    with pytest.raises(ValueError):
        registry.register(_ShadowEvent, name="_SampleEvent")


@pytest.mark.asyncio
async def test_in_process_bus_dispatches_to_all_subscribers():
    bus = InProcessEventBus()
    seen: list[_SampleEvent] = []

    async def handler_a(event: _SampleEvent) -> None:
        seen.append(event)

    async def handler_b(event: _SampleEvent) -> None:
        seen.append(event)

    bus.subscribe(_SampleEvent, handler_a)
    bus.subscribe(_SampleEvent, handler_b)
    event = _SampleEvent(
        aggregate_id=UUID(int=1), label="x", occurred_at=datetime.now(timezone.utc)
    )

    result = await bus.dispatch(event)

    assert result.ok is True
    assert result.succeeded == 2
    assert len(seen) == 2


@pytest.mark.asyncio
async def test_in_process_bus_isolates_handler_failures():
    bus = InProcessEventBus()
    sibling_ran = False

    async def failing(event: _SampleEvent) -> None:
        raise RuntimeError("boom")

    async def sibling(event: _SampleEvent) -> None:
        nonlocal sibling_ran
        sibling_ran = True

    bus.subscribe(_SampleEvent, failing)
    bus.subscribe(_SampleEvent, sibling)
    event = _SampleEvent(
        aggregate_id=UUID(int=1), label="x", occurred_at=datetime.now(timezone.utc)
    )

    result = await bus.dispatch(event)

    assert sibling_ran is True
    assert result.ok is False
    assert len(result.errors) == 1


class _FrozenClock(Clock):
    def __init__(self, at: datetime) -> None:
        self._at = at

    def now(self) -> datetime:
        return self._at


class _InMemoryOutboxRepository:
    def __init__(self, seed: list[OutboxRecord]) -> None:
        self._pending = list(seed)
        self.published: list[UUID] = []
        self.failed: list[tuple[UUID, str, int]] = []

    async def add_many(self, records):
        self._pending.extend(records)

    async def fetch_pending(self, *, batch_size: int):
        batch, self._pending = self._pending[:batch_size], self._pending[batch_size:]
        return batch

    async def mark_published(self, record_id: UUID, *, at: datetime) -> None:
        self.published.append(record_id)

    async def mark_failed(self, record_id: UUID, *, error: str, attempts: int) -> None:
        self.failed.append((record_id, error, attempts))


@pytest.mark.asyncio
async def test_outbox_relay_dispatches_pending_and_marks_published():
    registry = EventRegistry()
    registry.register(_SampleEvent)
    bus = InProcessEventBus()
    seen: list[_SampleEvent] = []

    async def handler(event: _SampleEvent) -> None:
        seen.append(event)

    bus.subscribe(_SampleEvent, handler)

    original = _SampleEvent(
        aggregate_id=UUID(int=7),
        label="hi",
        occurred_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    record = OutboxRecord(
        id=UUID(int=99),
        event_type=registry.name_for(type(original)),
        payload=registry.serialize(original),
        occurred_at=original.occurred_at,
    )
    repo = _InMemoryOutboxRepository([record])
    clock = _FrozenClock(datetime(2026, 1, 2, tzinfo=timezone.utc))

    relay = OutboxRelay(outbox=repo, bus=bus, registry=registry, clock=clock)
    published = await relay.relay_once()

    assert published == 1
    assert seen == [original]
    assert repo.published == [record.id]
    assert repo.failed == []


@pytest.mark.asyncio
async def test_outbox_relay_marks_failed_when_handler_raises():
    registry = EventRegistry()
    registry.register(_SampleEvent)
    bus = InProcessEventBus()

    async def boom(event: _SampleEvent) -> None:
        raise RuntimeError("kaboom")

    bus.subscribe(_SampleEvent, boom)

    original = _SampleEvent(
        aggregate_id=UUID(int=7),
        label="hi",
        occurred_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    record = OutboxRecord(
        id=UUID(int=99),
        event_type=registry.name_for(type(original)),
        payload=registry.serialize(original),
        occurred_at=original.occurred_at,
    )
    repo = _InMemoryOutboxRepository([record])
    relay = OutboxRelay(
        outbox=repo,
        bus=bus,
        registry=registry,
        clock=_FrozenClock(datetime(2026, 1, 2, tzinfo=timezone.utc)),
    )

    published = await relay.relay_once()

    assert published == 0
    assert repo.published == []
    assert repo.failed and repo.failed[0][0] == record.id


def test_dispatch_result_ok_flag():
    assert DispatchResult(succeeded=1, errors=[]).ok is True
    assert DispatchResult(succeeded=0, errors=[RuntimeError()]).ok is False
