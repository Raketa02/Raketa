from __future__ import annotations

from collections.abc import Iterable

from app.application.events.envelope import SerializedEventEnvelope
from app.application.ports.events import EventCodec, OutboxWriter
from app.shared.domain import DomainEvent
from app.shared.ids import new_uuid


class EventPublisher:
    """Writes released domain events in the aggregate transaction."""

    def __init__(
        self,
        *,
        outbox: OutboxWriter,
        codec: EventCodec,
    ) -> None:
        self._outbox = outbox
        self._codec = codec

    async def publish(self, event: DomainEvent) -> None:
        await self.publish_many([event])

    async def publish_many(self, events: Iterable[DomainEvent]) -> None:
        records: list[SerializedEventEnvelope] = []
        for event in events:
            encoded = self._codec.encode(event)
            records.append(
                SerializedEventEnvelope(
                    id=new_uuid(),
                    event_type=encoded.event_type,
                    schema_version=encoded.schema_version,
                    payload=encoded.payload,
                    occurred_at=event.occurred_at,
                )
            )
        if records:
            await self._outbox.add_many(records)
