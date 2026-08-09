from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.events.envelope import SerializedEventEnvelope
from app.infrastructure.events.event_delivery_model import EventOutboxORM


class SqlAlchemyOutboxRepository:
    """SQLAlchemy adapter for transactional outbox rows."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_many(self, records: Iterable[SerializedEventEnvelope]) -> None:
        rows = [
            EventOutboxORM(
                id=record.id,
                event_type=record.event_type,
                schema_version=record.schema_version,
                payload=record.payload,
                occurred_at=record.occurred_at,
                attempts=record.attempts,
            )
            for record in records
        ]
        if rows:
            self._session.add_all(rows)

    async def fetch_pending(
        self,
        *,
        batch_size: int,
    ) -> list[SerializedEventEnvelope]:
        stmt = (
            select(EventOutboxORM)
            .where(EventOutboxORM.published_at.is_(None))
            .order_by(EventOutboxORM.created_at, EventOutboxORM.id)
            .limit(batch_size)
            .with_for_update(skip_locked=True)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_envelope(row) for row in rows]

    async def mark_published(self, event_id: UUID, *, at: datetime) -> None:
        await self._session.execute(
            update(EventOutboxORM)
            .where(EventOutboxORM.id == event_id)
            .values(
                published_at=at,
                last_error=None,
            )
        )
        await self._session.commit()

    async def mark_failed(
        self,
        event_id: UUID,
        *,
        error: str,
        attempts: int,
    ) -> None:
        await self._session.execute(
            update(EventOutboxORM)
            .where(EventOutboxORM.id == event_id)
            .values(
                attempts=attempts,
                last_error=error,
            )
        )
        await self._session.commit()


def _to_envelope(row: EventOutboxORM) -> SerializedEventEnvelope:
    return SerializedEventEnvelope(
        id=row.id,
        event_type=row.event_type,
        schema_version=row.schema_version,
        payload=dict(row.payload),
        occurred_at=row.occurred_at,
        attempts=row.attempts,
        published_at=row.published_at,
        last_error=row.last_error,
        created_at=row.created_at,
    )
