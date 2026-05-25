from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.events.sqlalchemy_outbox_model import EventOutboxORM
from app.shared.events import OutboxRecord


class SqlAlchemyOutboxRepository:
    """Adapter implementing `OutboxRepository` for the `event_outbox` table.

    `add_many` runs on the session that the use case is already using, so
    inserts join the active transaction. The poll / mark methods take a
    fresh session per relay tick to avoid sharing connections with request
    handlers.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_many(self, records: Iterable[OutboxRecord]) -> None:
        rows = [
            EventOutboxORM(
                id=record.id,
                event_type=record.event_type,
                payload=record.payload,
                occurred_at=record.occurred_at,
                attempts=record.attempts,
            )
            for record in records
        ]
        if not rows:
            return
        self._session.add_all(rows)

    async def fetch_pending(self, *, batch_size: int) -> list[OutboxRecord]:
        stmt = (
            select(EventOutboxORM)
            .where(EventOutboxORM.published_at.is_(None))
            .order_by(EventOutboxORM.created_at)
            .limit(batch_size)
            .with_for_update(skip_locked=True)
        )
        result = await self._session.execute(stmt)
        rows = result.scalars().all()
        return [_to_record(row) for row in rows]

    async def mark_published(self, record_id: UUID, *, at: datetime) -> None:
        await self._session.execute(
            update(EventOutboxORM)
            .where(EventOutboxORM.id == record_id)
            .values(published_at=at, last_error=None)
        )
        await self._session.commit()

    async def mark_failed(
        self, record_id: UUID, *, error: str, attempts: int
    ) -> None:
        await self._session.execute(
            update(EventOutboxORM)
            .where(EventOutboxORM.id == record_id)
            .values(attempts=attempts, last_error=error)
        )
        await self._session.commit()


def _to_record(row: EventOutboxORM) -> OutboxRecord:
    return OutboxRecord(
        id=row.id,
        event_type=row.event_type,
        payload=dict(row.payload),
        occurred_at=row.occurred_at,
        attempts=row.attempts,
        published_at=row.published_at,
        last_error=row.last_error,
        created_at=row.created_at,
    )
