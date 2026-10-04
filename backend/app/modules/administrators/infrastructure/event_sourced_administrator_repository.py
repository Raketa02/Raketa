"""The Administrator repository: the stream, and the row written beside it.

The same shape as the Club and Group repositories — the aggregate type spelled
once, state rebuilt by replay, the version remembered from the load and expected
by the append (``docs/adr/0018``) — and **its projection is written by ``save``,
in the caller's transaction**, so the club's list and the guard read an act the
moment it commits. The row is written from the aggregate's state after the
events rather than event by event: every field on it is a fold of the stream,
except ``last_used_at``, which only an acceptance and the guard move.

**Constructed per request**, for the reason every aggregate repository here is:
the versions it remembers belong to one unit of work.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports import DomainEventPublisher, DomainEventStore
from app.modules.administrators.domain.administrator import Administrator
from app.modules.administrators.domain.events import (
    AdministratorInvited,
    InvitationAccepted,
)
from app.modules.administrators.infrastructure.administrator_model import (
    AdministratorORM,
)
from app.modules.users.domain.value_objects import Email

ADMINISTRATOR_AGGREGATE = "administrator"


class EventSourcedAdministratorRepository:
    """``AdministratorRepository`` over ``DomainEventStore`` and its row."""

    def __init__(
        self,
        *,
        session: AsyncSession,
        event_store: DomainEventStore,
        events: DomainEventPublisher,
    ) -> None:
        self._session = session
        self._event_store = event_store
        self._events = events
        self._versions: dict[UUID, int] = {}

    async def load(self, administrator_id: UUID) -> Optional[Administrator]:
        stored = await self._event_store.load_stream(
            aggregate_type=ADMINISTRATOR_AGGREGATE, aggregate_id=administrator_id
        )
        if not stored:
            return None
        administrator = Administrator.from_history(record.event for record in stored)
        self._versions[administrator.id] = administrator.version
        return administrator

    async def at_club(self, club_id: UUID, email: Email) -> Optional[Administrator]:
        found = await self._session.scalar(
            select(AdministratorORM.id).where(
                AdministratorORM.club_id == club_id,
                AdministratorORM.email == email.value,
            )
        )
        return None if found is None else await self.load(found)

    async def save(self, administrator: Administrator) -> None:
        pending = administrator.pull_events()
        if not pending:
            return
        await self._event_store.append(
            aggregate_type=ADMINISTRATOR_AGGREGATE,
            aggregate_id=administrator.id,
            expected_version=self._versions.get(administrator.id, 0),
            events=pending,
        )
        await self._events.publish_many(pending)
        row = await self._session.get(AdministratorORM, administrator.id)
        if row is None:
            if not isinstance(pending[0], AdministratorInvited):
                raise RuntimeError(
                    f"administrator {administrator.id} has no row to land on"
                )
            row = AdministratorORM(id=administrator.id, club_id=administrator.club_id)
            self._session.add(row)
        row.email = administrator.email.value
        row.name = administrator.name.value
        row.state = administrator.state.value
        row.account_id = administrator.account_id
        row.expires_at = administrator.expires_at
        row.reset_pending = administrator.reset_pending
        for event in pending:
            if isinstance(event, InvitationAccepted):
                # Taking an invitation up is the first use of the profile it
                # opens, so the club's list reads *active · today* at once.
                row.last_used_at = event.occurred_at
        await self._session.flush()
        # Deliberately no commit: the transaction boundary is the use case's.
        self._versions[administrator.id] = administrator.version
