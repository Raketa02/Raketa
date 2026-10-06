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
from app.kernel import Clock
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


@dataclass(frozen=True)
class _NullableEvent:
    aggregate_id: UUID
    actor_id: UUID | None
    settled_at: datetime | None
    occurred_at: datetime


@pytest.mark.parametrize(
    "event",
    [
        _NullableEvent(
            aggregate_id=UUID(int=1),
            actor_id=UUID(int=2),
            settled_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
            occurred_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        ),
        _NullableEvent(
            aggregate_id=UUID(int=1),
            actor_id=None,
            settled_at=None,
            occurred_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        ),
    ],
    ids=["filled", "null"],
)
def test_a_nullable_id_or_instant_decodes_as_the_type_it_was_declared(event):
    """``UUID | None`` is not ``UUID``, and a codec that matched the hint by
    identity left the filled arm as a string — equal to no id, unsortable beside
    one ([#408](https://github.com/Raketa02/Raketa/issues/408))."""

    catalog = EventCatalog()
    catalog.register(_NullableEvent, name="tests.nullable", version=1)
    codec = JsonEventCodec(catalog)

    encoded = codec.encode(event)
    decoded = codec.decode(
        SerializedEventEnvelope(
            id=UUID(int=99),
            event_type=encoded.event_type,
            schema_version=encoded.schema_version,
            payload=encoded.payload,
            occurred_at=event.occurred_at,
        )
    )

    assert decoded == event
    assert type(decoded.actor_id) is type(event.actor_id)
    assert type(decoded.settled_at) is type(event.settled_at)


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
        #: Events another deliverer holds — read by this batch's fetch, and
        #: taken by somebody else once its first commit released them.
        self.taken: set[UUID] = set()

    async def claim(self, event_id) -> bool:
        return (
            event_id not in self.taken and self.records[event_id].published_at is None
        )

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


class _CountingUnitOfWork:
    """The transaction the handlers ran in, as a pair of counters.

    A handler that writes commits with the row that told it to, so what is worth
    asserting here is that a **failed** delivery rolls back before its attempt is
    recorded — otherwise half of what the handler wrote would be committed by the
    update that says it failed.
    """

    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0

    async def commit(self) -> None:
        self.commits += 1

    async def flush(self) -> None:
        return None

    async def rollback(self) -> None:
        self.rollbacks += 1


def _batch(store, dispatcher, uow=None):
    return EventBatch(
        outbox=store,
        codec=_codec(),
        dispatcher=dispatcher,
        uow=uow or _CountingUnitOfWork(),
        clock=_FrozenClock(datetime(2026, 1, 2, tzinfo=timezone.utc)),
    )


@pytest.mark.asyncio
async def test_a_failed_delivery_rolls_back_before_the_attempt_is_recorded():
    """``docs/adr/0146`` §5 put the first *writing* subscriber on this loop."""

    store = _InMemoryStore([_record()])
    dispatcher = EventDispatcher()
    uow = _CountingUnitOfWork()

    async def handler(event: _SampleEvent, context: DeliveryContext) -> None:
        raise RuntimeError("half a system line")

    dispatcher.subscribe(_SampleEvent, handler)
    published = await _batch(store, dispatcher, uow).execute(worker_id="test")

    assert published == 0
    assert uow.rollbacks == 1


@pytest.mark.asyncio
async def test_a_successful_delivery_is_not_rolled_back():
    store = _InMemoryStore([_record()])
    dispatcher = EventDispatcher()
    uow = _CountingUnitOfWork()

    async def handler(event: _SampleEvent, context: DeliveryContext) -> None:
        return None

    dispatcher.subscribe(_SampleEvent, handler)
    await _batch(store, dispatcher, uow).execute(worker_id="test")

    assert uow.rollbacks == 0


@pytest.mark.asyncio
async def test_an_event_another_deliverer_has_taken_is_left_to_it():
    """**A batch claims each event as it reaches it.** Its first commit releases
    every row its fetch locked, so another deliverer — the API's worker beside a
    seed run, or a second API process — can take the rest of the batch; and an
    event delivered twice is every side effect twice."""

    store = _InMemoryStore([_record()])
    store.taken.add(UUID(int=99))
    dispatcher = EventDispatcher()
    delivered: list[DeliveryContext] = []

    async def handler(event: _SampleEvent, context: DeliveryContext) -> None:
        delivered.append(context)

    dispatcher.subscribe(_SampleEvent, handler)
    published = await _batch(store, dispatcher).execute(worker_id="test")

    assert published == 0
    assert delivered == []
    assert store.records[UUID(int=99)].attempts == 0


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
