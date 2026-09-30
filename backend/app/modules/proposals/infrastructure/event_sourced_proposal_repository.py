"""The Proposal repository: the stream, and the two projections written beside it.

The same shape as the other aggregate repositories — the aggregate type spelled
once, state rebuilt by replay, the version remembered from the load and expected
by the append (``docs/adr/0018``) — and, like a group's, **its projections are
written by ``save``, in the caller's transaction**, so a yes is in the player's
live list and the cap's count the moment it commits. The pools row is one of
them: the first game proposed in a pool writes it.

**Constructed per unit of work**, for the reason every aggregate repository here
is: the versions it remembers belong to one transaction.
"""

from __future__ import annotations

from datetime import datetime
from typing import final
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Executable

from app.application.ports import DomainEventPublisher, DomainEventStore
from app.modules.proposals.domain.events import (
    NoSaid,
    ProposalExpired,
    ProposalMade,
    ProposalWithdrawn,
    VersionDealt,
    YesSaid,
    YesWithdrawn,
)
from app.modules.proposals.domain.proposal import Ending, Proposal
from app.modules.proposals.infrastructure.proposal_models import (
    PoolORM,
    ProposalORM,
    ProposalPersonORM,
)
from app.shared.domain import DomainEvent

PROPOSAL_AGGREGATE = "proposal"


@final
class EventSourcedProposalRepository:
    """``ProposalRepository`` over ``DomainEventStore`` and the two projections."""

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

    async def load(self, proposal_id: UUID) -> Proposal | None:
        stored = await self._event_store.load_stream(
            aggregate_type=PROPOSAL_AGGREGATE, aggregate_id=proposal_id
        )
        if not stored:
            return None
        proposal = Proposal.from_history(record.event for record in stored)
        self._versions[proposal_id] = proposal.version
        return proposal

    async def save(self, proposal: Proposal) -> None:
        pending = proposal.pull_events()
        if not pending:
            return
        await self._event_store.append(
            aggregate_type=PROPOSAL_AGGREGATE,
            aggregate_id=proposal.proposal_id,
            expected_version=self._versions.get(proposal.proposal_id, 0),
            events=pending,
        )
        await self._events.publish_many(pending)
        for event in pending:
            await self._project(event)
        await self._session.flush()
        # Deliberately no commit: the transaction boundary is the use case's.
        self._versions[proposal.proposal_id] = proposal.version

    async def _project(self, event: DomainEvent) -> None:
        if isinstance(event, ProposalMade):
            if await self._session.get(PoolORM, event.pool_id) is None:
                # The first game proposed in a pool writes its row.
                self._session.add(
                    PoolORM(
                        id=event.pool_id,
                        kind=event.pool_kind,
                        opened_at=event.occurred_at,
                    )
                )
                await self._session.flush()
            self._session.add(
                ProposalORM(
                    id=event.proposal_id,
                    pool_id=event.pool_id,
                    origin=event.origin,
                    poster_id=event.poster_id,
                    sport=event.sport,
                    kind=event.kind,
                    club_id=event.club_id,
                    start=event.start,
                    share_grosze=event.share_grosze,
                    book_by=event.book_by,
                    made_at=event.occurred_at,
                )
            )
            # The game's row before its first person's, which references it.
            await self._session.flush()
        elif isinstance(event, VersionDealt):
            for player_id in event.player_ids:
                self._session.add(
                    ProposalPersonORM(
                        proposal_id=event.proposal_id,
                        player_id=player_id,
                        version=event.number,
                    )
                )
        elif isinstance(event, YesSaid):
            answered = await self._answer(
                event.proposal_id, event.player_id, "YES", event.occurred_at
            )
            if not answered:
                # In without a version: a poster.
                self._session.add(
                    ProposalPersonORM(
                        proposal_id=event.proposal_id,
                        player_id=event.player_id,
                        answer="YES",
                        answered_at=event.occurred_at,
                    )
                )
        elif isinstance(event, NoSaid):
            await self._answer(
                event.proposal_id, event.player_id, "NO", event.occurred_at
            )
        elif isinstance(event, YesWithdrawn):
            await self._answer(
                event.proposal_id, event.player_id, "WITHDRAWN", event.occurred_at
            )
        elif isinstance(event, ProposalWithdrawn):
            await self._end(event.proposal_id, Ending.WITHDRAWN)
        elif isinstance(event, ProposalExpired):
            await self._end(event.proposal_id, Ending.EXPIRED)
        else:
            raise TypeError(f"Unsupported proposal event {event!r}")

    async def _answer(
        self, proposal_id: UUID, player_id: UUID, answer: str, at: datetime
    ) -> bool:
        """Record a person's answer on their row. Whether they had one."""

        result = await self._statement(
            update(ProposalPersonORM)
            .where(
                ProposalPersonORM.proposal_id == proposal_id,
                ProposalPersonORM.player_id == player_id,
            )
            .values(answer=answer, answered_at=at)
        )
        return bool(getattr(result, "rowcount", 0))

    async def _end(self, proposal_id: UUID, ending: Ending) -> None:
        await self._statement(
            update(ProposalORM)
            .where(ProposalORM.id == proposal_id)
            .values(ended=ending.value)
        )

    async def _statement(self, statement: Executable) -> object:
        # A statement, not a unit-of-work change, so whatever this save added
        # before it is flushed first — the row it touches may be one.
        await self._session.flush()
        return await self._session.execute(statement)
