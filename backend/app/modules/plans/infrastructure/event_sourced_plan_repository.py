"""The Plan repository and directory, over the event store.

The same fifteen lines the other aggregate repositories have — which aggregate
type the streams are filed under, that state is rebuilt by replaying them, and
what version the next append expects. ADR-0018 declined a generic event-sourced
base deliberately.

**Its own aggregate type**, spelled here once and nowhere else.

**There is no lookup by payload here, and that is the whole dividend of keying on
the game's id.** ``games`` matches a serialized challenge id to make its opening
idempotent and a serialized court to find a player's streams; ``conversations``
carries a row with two foreign keys. A plan's stream id **is** its game's, so
*this game's plan* is a stream read and *these games' plans* is an ``IN`` on the
aggregate id — the two reads a payload match would otherwise have to be written
and guarded for.

**``load`` answers an unwritten plan rather than ``None``.** A plan is born by
being used, so *nothing agreed yet* is a plan with nothing in it: the three write
paths start from it, and a repository that answered ``None`` would make each of
them spell the birth. The **directory** never returns one, and it needs no filter
to promise that — a game nobody has agreed anything about has no stream.

**The version is recovered, not taken**, so this must be constructed **per
request** from the session, exactly as the event store dependency is.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Collection, final
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.events.envelope import SerializedEventEnvelope
from app.application.ports import DomainEventPublisher, DomainEventStore
from app.application.ports.events import EventCodec
from app.infrastructure.events.event_store_model import EventStoreORM
from app.modules.plans.domain.plan import Plan
from app.shared.domain import DomainEvent

PLAN_AGGREGATE = "plan"


@final
class EventSourcedPlanRepository:
    """``PlanRepository`` over ``DomainEventStore``."""

    def __init__(
        self,
        *,
        event_store: DomainEventStore,
        events: DomainEventPublisher,
    ) -> None:
        self._event_store = event_store
        self._events = events
        # Game id -> the stream version this request has seen. Read by ``save``
        # as the expected version, and **zero for a plan that does not exist
        # yet** — which is what makes the first recording an append against an
        # empty stream rather than a create.
        self._versions: dict[UUID, int] = {}

    async def load(self, game_id: UUID) -> Plan:
        stored = await self._event_store.load_stream(
            aggregate_type=PLAN_AGGREGATE,
            aggregate_id=game_id,
        )
        plan = (
            Plan.unwritten(game_id)
            if not stored
            else Plan.from_history(record.event for record in stored)
        )
        self._remember(plan)
        return plan

    async def save(self, plan: Plan) -> None:
        pending = plan.pull_events()
        if not pending:
            # **A write of the value already there records nothing**, so this is
            # the ordinary path rather than an edge: the aggregate answered that
            # nothing changed, and there is no stream to append to.
            return

        await self._event_store.append(
            aggregate_type=PLAN_AGGREGATE,
            aggregate_id=plan.id,
            expected_version=self._versions.get(plan.id, 0),
            events=pending,
        )
        await self._events.publish_many(pending)
        # Deliberately no commit: the transaction boundary is the use case's.
        self._remember(plan)

    def _remember(self, plan: Plan) -> None:
        self._versions[plan.id] = plan.version


@final
class EventSourcedPlanDirectory:
    """``PlanDirectory`` over ``event_store``. **One statement, whatever the list.**

    It reads the rows itself rather than folding through the repository, and the
    difference from ``conversations``' directory is the reason: there the
    aggregates come back with stream versions a caller may be about to append
    against, so two readers would be two answers to *what version have I seen*.
    Nothing appends to a plan it read from here — the list read is a read — so
    the cheaper shape is also the honest one.
    """

    def __init__(self, session: AsyncSession, codec: EventCodec) -> None:
        self._session = session
        self._codec = codec

    async def for_games(self, game_ids: Collection[UUID]) -> tuple[Plan, ...]:
        """Every plan among these games, folded whole.

        **A game with nothing agreed has no stream and is simply absent** — which
        is *no plan* spelled once, by the store rather than by a filter.

        Ordered by ``version`` within each stream, which is what a fold needs and
        the only order it may be handed: a replay is a sequence and not a set.
        """

        wanted = sorted(set(game_ids))
        if not wanted:
            return ()

        rows = await self._session.execute(
            select(EventStoreORM)
            .where(
                EventStoreORM.aggregate_type == PLAN_AGGREGATE,
                EventStoreORM.aggregate_id.in_(wanted),
            )
            .order_by(EventStoreORM.version)
        )
        streams: dict[UUID, list[DomainEvent]] = defaultdict(list)
        for row in rows.scalars().all():
            streams[row.aggregate_id].append(_decode(self._codec, row))
        return tuple(Plan.from_history(events) for events in streams.values())


def _decode(codec: EventCodec, row: EventStoreORM) -> DomainEvent:
    return codec.decode(
        SerializedEventEnvelope(
            id=row.id,
            event_type=row.event_type,
            schema_version=row.schema_version,
            payload=dict(row.payload),
            occurred_at=row.occurred_at,
            created_at=row.created_at,
        )
    )
