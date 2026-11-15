from __future__ import annotations

from collections.abc import Collection, Iterable, Mapping
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.events.envelope import SerializedEventEnvelope
from app.application.events.store import (
    EventStreamVersionConflict,
    StoredDomainEvent,
)
from app.application.ports.events import EventCodec
from app.infrastructure.events.event_store_model import EventStoreORM
from app.shared.domain import DomainEvent
from app.shared.ids import new_uuid


class SqlAlchemyEventStore:
    """SQLAlchemy adapter for append-only aggregate event streams."""

    def __init__(self, session: AsyncSession, codec: EventCodec) -> None:
        self._session = session
        self._codec = codec

    async def append(
        self,
        *,
        aggregate_type: str,
        aggregate_id: UUID,
        expected_version: int,
        events: Iterable[DomainEvent],
    ) -> list[StoredDomainEvent]:
        pending = list(events)
        if not pending:
            return []

        current_version = await self._current_version(
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
        )
        if current_version != expected_version:
            raise EventStreamVersionConflict(
                f"Expected {aggregate_type}/{aggregate_id} at version "
                f"{expected_version}, found {current_version}"
            )

        rows: list[EventStoreORM] = []
        for offset, event in enumerate(pending, start=1):
            encoded = self._codec.encode(event)
            rows.append(
                EventStoreORM(
                    id=new_uuid(),
                    aggregate_type=aggregate_type,
                    aggregate_id=aggregate_id,
                    version=expected_version + offset,
                    event_type=encoded.event_type,
                    schema_version=encoded.schema_version,
                    payload=encoded.payload,
                    occurred_at=event.occurred_at,
                )
            )

        self._session.add_all(rows)
        try:
            await self._session.flush(objects=rows)
        except IntegrityError as exc:
            raise EventStreamVersionConflict(
                f"Concurrent modification detected for {aggregate_type}/{aggregate_id}"
            ) from exc
        return [_to_stored(row, self._codec) for row in rows]

    async def load_stream(
        self, *, aggregate_type: str, aggregate_id: UUID
    ) -> list[StoredDomainEvent]:
        result = await self._session.execute(
            select(EventStoreORM)
            .where(
                EventStoreORM.aggregate_type == aggregate_type,
                EventStoreORM.aggregate_id == aggregate_id,
            )
            .order_by(EventStoreORM.version)
        )
        return [_to_stored(row, self._codec) for row in result.scalars().all()]

    async def streams_present(
        self, *, aggregate_type: str, aggregate_ids: Collection[UUID]
    ) -> frozenset[UUID]:
        # Deduplicated in the caller's order, so a caller's declared walk is the
        # order the statement binds its ids in.
        wanted = list(dict.fromkeys(aggregate_ids))
        if not wanted:
            return frozenset()
        # The leading two columns of `ix_event_store_stream`, so each id is an
        # index probe — the read `load_stream` makes, once for the batch, with
        # no row decoded.
        result = await self._session.execute(
            select(EventStoreORM.aggregate_id)
            .where(
                EventStoreORM.aggregate_type == aggregate_type,
                EventStoreORM.aggregate_id.in_(wanted),
            )
            .distinct()
        )
        return frozenset(result.scalars().all())

    async def find_aggregate_ids_by_first_event(
        self, *, aggregate_type: str, payload_equals: Mapping[str, str]
    ) -> list[UUID]:
        query = select(EventStoreORM.aggregate_id).where(
            EventStoreORM.aggregate_type == aggregate_type,
            EventStoreORM.version == 1,
        )
        for key, value in payload_equals.items():
            query = query.where(EventStoreORM.payload[key].as_string() == value)
        # Append order, not domain time. This read crosses streams, and
        # `occurred_at` is not a total order over them: two streams opened in one
        # commit share an instant, and Postgres is free to return such a tie
        # either way round. `_newest_open_by_sport` scans this list in reverse to
        # find the run to resume, so an undefined tie is an undefined answer.
        result = await self._session.execute(query.order_by(EventStoreORM.sequence_no))
        return list(result.scalars().all())

    async def _current_version(self, *, aggregate_type: str, aggregate_id: UUID) -> int:
        result = await self._session.execute(
            select(func.coalesce(func.max(EventStoreORM.version), 0)).where(
                EventStoreORM.aggregate_type == aggregate_type,
                EventStoreORM.aggregate_id == aggregate_id,
            )
        )
        return int(result.scalar_one())


def _to_stored(row: EventStoreORM, codec: EventCodec) -> StoredDomainEvent:
    event = codec.decode(
        SerializedEventEnvelope(
            id=row.id,
            event_type=row.event_type,
            schema_version=row.schema_version,
            payload=dict(row.payload),
            occurred_at=row.occurred_at,
            created_at=row.created_at,
        )
    )
    return StoredDomainEvent(
        id=row.id,
        sequence_no=row.sequence_no,
        aggregate_type=row.aggregate_type,
        aggregate_id=row.aggregate_id,
        version=row.version,
        event=event,
        occurred_at=row.occurred_at,
        created_at=row.created_at,
    )
