from __future__ import annotations

import asyncio
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from uuid import UUID

import pytest

from app.application.events import (
    EventDispatcher,
    DeliveryContext,
    EventCatalog,
    SerializedEventEnvelope,
)
from app.application.events.deliver_event_batch import EventBatch
from app.infrastructure.events.json_event_codec import JsonEventCodec
from app.infrastructure.events.transactional_publisher import (
    EventPublisher,
)
from app.shared.clock import Clock
from app.shared.domain import EventRecorder


@dataclass(frozen=True)
class _SampleEvent:
    aggregate_id: UUID
    label: str
    occurred_at: datetime


class _FrozenClock(Clock):
    def __init__(self, at: datetime) -> None:
        self._at = at

    def now(self) -> datetime:
        return self._at


def _codec() -> JsonEventCodec:
    catalog = EventCatalog()
    catalog.register(_SampleEvent, name="tests.sample", version=1)
    return JsonEventCodec(catalog)


def _event() -> _SampleEvent:
    return _SampleEvent(
        aggregate_id=UUID(int=42),
        label="hello",
        occurred_at=datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc),
    )


def _record(*, payload: dict | None = None, attempts: int = 0):
    encoded = _codec().encode(_event())
    return SerializedEventEnvelope(
        id=UUID(int=99),
        event_type=encoded.event_type,
        schema_version=encoded.schema_version,
        payload=payload or encoded.payload,
        occurred_at=_event().occurred_at,
        attempts=attempts,
    )


def test_event_recorder_drains_then_resets():
    recorder = EventRecorder()
    event = _event()
    recorder.record(event)
    assert recorder.pull() == [event]
    assert recorder.pull() == []


def test_catalog_and_codec_roundtrip_stable_contract():
    codec = _codec()
    encoded = codec.encode(_event())
    record = _record()

    assert encoded.event_type == "tests.sample"
    assert encoded.schema_version == 1
    assert codec.decode(record) == _event()


def test_catalog_rejects_conflicting_contracts():
    catalog = EventCatalog()
    catalog.register(_SampleEvent, name="tests.sample", version=1)

    @dataclass(frozen=True)
    class _ShadowEvent:
        occurred_at: datetime

    with pytest.raises(ValueError):
        catalog.register(_ShadowEvent, name="tests.sample", version=1)


@pytest.mark.asyncio
async def test_dispatcher_provides_delivery_context_and_reports_missing_handlers():
    dispatcher = EventDispatcher()
    context = DeliveryContext(
        event_id=UUID(int=1), attempt=2, occurred_at=_event().occurred_at
    )
    seen: list[DeliveryContext] = []

    async def handler(event: _SampleEvent, delivered: DeliveryContext) -> None:
        seen.append(delivered)

    dispatcher.subscribe(_SampleEvent, handler)
    assert (await dispatcher.dispatch(_event(), context)).ok is True
    assert seen == [context]
    assert (
        await EventDispatcher().dispatch(_event(), context)
    ).missing_handlers is True


@pytest.mark.asyncio
async def test_dispatcher_isolates_exception_handlers_without_swallowing_cancellation():
    dispatcher = EventDispatcher()
    sibling_ran = False

    async def failing(event: _SampleEvent, context: DeliveryContext) -> None:
        raise RuntimeError("boom")

    async def sibling(event: _SampleEvent, context: DeliveryContext) -> None:
        nonlocal sibling_ran
        sibling_ran = True

    dispatcher.subscribe(_SampleEvent, failing)
    dispatcher.subscribe(_SampleEvent, sibling)
    result = await dispatcher.dispatch(
        _event(), DeliveryContext(UUID(int=1), 1, _event().occurred_at)
    )

    assert sibling_ran is True
    assert result.ok is False
    assert len(result.errors) == 1


@pytest.mark.asyncio
async def test_dispatcher_propagates_cancellation():
    dispatcher = EventDispatcher()

    async def cancelled(event: _SampleEvent, context: DeliveryContext) -> None:
        raise asyncio.CancelledError

    dispatcher.subscribe(_SampleEvent, cancelled)
    with pytest.raises(asyncio.CancelledError):
        await dispatcher.dispatch(
            _event(), DeliveryContext(UUID(int=1), 1, _event().occurred_at)
        )


class _InMemoryStore:
    def __init__(self, seed: list[SerializedEventEnvelope]) -> None:
        self.records = {record.id: record for record in seed}

    async def add_many(self, records) -> None:
        self.records.update({record.id: record for record in records})

    async def fetch_pending(self, *, batch_size):
        return [
            record for record in self.records.values() if record.published_at is None
        ][:batch_size]

    async def mark_published(self, event_id, *, at):
        record = self.records[event_id]
        self.records[event_id] = replace(
            record,
            published_at=at,
            last_error=None,
        )

    async def mark_failed(self, event_id, *, error, attempts):
        record = self.records[event_id]
        self.records[event_id] = replace(
            record,
            attempts=attempts,
            last_error=error,
        )


def _batch(store, dispatcher):
    return EventBatch(
        outbox=store,
        codec=_codec(),
        dispatcher=dispatcher,
        clock=_FrozenClock(datetime(2026, 1, 2, tzinfo=timezone.utc)),
    )


@pytest.mark.asyncio
async def test_deliver_event_batch_publishes_successful_delivery():
    store = _InMemoryStore([_record()])
    dispatcher = EventDispatcher()

    async def handler(event: _SampleEvent, context: DeliveryContext) -> None:
        return None

    dispatcher.subscribe(_SampleEvent, handler)
    published = await _batch(store, dispatcher).execute(worker_id="test")

    assert published == 1
    assert store.records[UUID(int=99)].published_at == datetime(
        2026, 1, 2, tzinfo=timezone.utc
    )
    assert store.records[UUID(int=99)].attempts == 0


@pytest.mark.asyncio
async def test_deliver_event_batch_records_failure_for_retry():
    dispatcher = EventDispatcher()

    async def failing(event: _SampleEvent, context: DeliveryContext) -> None:
        raise RuntimeError("kaboom")

    dispatcher.subscribe(_SampleEvent, failing)
    store = _InMemoryStore([_record()])
    await _batch(store, dispatcher).execute(worker_id="test")
    retried = store.records[UUID(int=99)]
    assert retried.published_at is None
    assert retried.attempts == 1
    assert retried.last_error is not None
    assert "kaboom" in retried.last_error


@pytest.mark.asyncio
async def test_deliver_event_batch_records_terminal_failures():
    malformed = _record(payload={"aggregate_id": "not-a-uuid"})
    malformed_store = _InMemoryStore([malformed])
    await _batch(malformed_store, EventDispatcher()).execute(
        worker_id="test"
    )
    assert malformed_store.records[malformed.id].published_at is None
    assert malformed_store.records[malformed.id].attempts == 1
    assert malformed_store.records[malformed.id].last_error is not None
    assert "decode failed" in malformed_store.records[malformed.id].last_error

    missing_store = _InMemoryStore([_record()])
    await _batch(missing_store, EventDispatcher()).execute(worker_id="test")
    missing = missing_store.records[UUID(int=99)]
    assert missing.published_at is None
    assert missing.attempts == 1
    assert missing.last_error is not None
    assert "MissingEventHandlerError" in missing.last_error


@pytest.mark.asyncio
async def test_transactional_publisher_writes_encoded_pending_envelope():
    store = _InMemoryStore([])
    publisher = EventPublisher(outbox=store, codec=_codec())

    await publisher.publish(_event())

    record = next(iter(store.records.values()))
    assert record.event_type == "tests.sample"
    assert record.schema_version == 1
    assert record.published_at is None
    assert record.attempts == 0
