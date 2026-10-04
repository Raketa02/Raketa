"""The Club repository: the stream, and the search row written beside it.

The same shape as the other aggregate repositories — the aggregate type spelled
once, state rebuilt by replay, the version remembered from the load and expected
by the append (``docs/adr/0018``) — plus the one thing a club needs that they do
not: **its search projection is written by ``save``, in the caller's
transaction** (``docs/adr/0182`` §2), so an edit is in the next search's answer
and there is no second call to forget.

**Constructed per request**, for the reason every aggregate repository here is:
the versions it remembers belong to one unit of work.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports import DomainEventPublisher, DomainEventStore
from app.modules.clubs.domain.club import Club
from app.modules.clubs.domain.events import ClubDetailsChanged, ClubRegistered
from app.modules.clubs.domain.folding import fold
from app.modules.clubs.infrastructure.club_model import ClubORM
from app.shared.domain import DomainEvent

CLUB_AGGREGATE = "club"


class EventSourcedClubRepository:
    """``ClubRepository`` over ``DomainEventStore`` and the ``clubs`` row."""

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

    async def load(self, club_id: UUID) -> Optional[Club]:
        stored = await self._event_store.load_stream(
            aggregate_type=CLUB_AGGREGATE, aggregate_id=club_id
        )
        if not stored:
            return None
        club = Club.from_history(record.event for record in stored)
        self._versions[club.id] = club.version
        return club

    async def save(self, club: Club) -> None:
        pending = club.pull_events()
        if not pending:
            return
        await self._event_store.append(
            aggregate_type=CLUB_AGGREGATE,
            aggregate_id=club.id,
            expected_version=self._versions.get(club.id, 0),
            events=pending,
        )
        await self._events.publish_many(pending)
        for event in pending:
            await self._project(event)
        # Deliberately no commit: the transaction boundary is the use case's.
        self._versions[club.id] = club.version

    async def _project(self, event: DomainEvent) -> None:
        if isinstance(event, ClubRegistered):
            row = ClubORM(id=event.club_id)
            self._session.add(row)
        elif isinstance(event, ClubDetailsChanged):
            found = await self._session.get(ClubORM, event.club_id)
            if found is None:
                raise RuntimeError(
                    f"the details of club {event.club_id} have no row to land on"
                )
            row = found
        else:
            raise TypeError(f"Unsupported club event {event!r}")
        row.name = event.name
        row.district = event.district
        row.city = event.city
        row.sports = list(event.sports)
        row.latitude = event.latitude
        row.longitude = event.longitude
        row.name_folded = fold(event.name)
        row.district_folded = fold(event.district)
        await self._session.flush()
