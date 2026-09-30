"""The Club courts repository: one stream per club, and nothing beside it.

The same shape as the other aggregate repositories — the aggregate type spelled
once, state rebuilt by replay, the version remembered from the load and expected
by the append (``docs/adr/0018``).

**Filed under the club's own id**, so *this club's courts* is a stream read.
**``load`` answers an unwritten aggregate rather than ``None``**, as the Plan's
does: a club that has done nothing here is a club with no courts, the write
paths all start from it, and a repository answering ``None`` would make each of
them spell the birth.

**Constructed per request**, for the reason every aggregate repository here is:
the versions it remembers belong to one unit of work.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.application.ports import DomainEventPublisher, DomainEventStore
from app.modules.clubs.domain.club_courts import ClubCourts

CLUB_COURTS_AGGREGATE = "club_courts"


@final
class EventSourcedClubCourtsRepository:
    """``ClubCourtsRepository`` over ``DomainEventStore``."""

    def __init__(
        self, *, event_store: DomainEventStore, events: DomainEventPublisher
    ) -> None:
        self._event_store = event_store
        self._events = events
        # Club id -> the stream version this unit of work has seen; **zero for a
        # club with no stream yet**, which makes the first act an append against
        # an empty stream rather than a create.
        self._versions: dict[UUID, int] = {}

    async def load(self, club_id: UUID) -> ClubCourts:
        stored = await self._event_store.load_stream(
            aggregate_type=CLUB_COURTS_AGGREGATE, aggregate_id=club_id
        )
        club = ClubCourts.from_history(club_id, (record.event for record in stored))
        self._versions[club_id] = club.version
        return club

    async def save(self, club: ClubCourts) -> None:
        pending = club.pull_events()
        if not pending:
            # A save that changed nothing records nothing, and this is the
            # ordinary path: the aggregate answered that nothing moved.
            return
        await self._event_store.append(
            aggregate_type=CLUB_COURTS_AGGREGATE,
            aggregate_id=club.club_id,
            expected_version=self._versions.get(club.club_id, 0),
            events=pending,
        )
        await self._events.publish_many(pending)
        # Deliberately no commit: the transaction boundary is the use case's.
        self._versions[club.club_id] = club.version
