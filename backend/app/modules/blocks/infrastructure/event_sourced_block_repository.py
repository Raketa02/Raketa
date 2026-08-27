"""The Block repository, over the event store.

The same fifteen lines the other four aggregate repositories have — which
aggregate-type string the streams are filed under, that state is rebuilt by
replaying them, and what version the next append expects. ADR-0018 declined a
generic event-sourced base deliberately: event-sourced-versus-persisted-with-
events is an open per-context decision, and a shared base would quietly answer it
for the contexts nobody has built yet. A fifth concrete adapter that reads
straight through is the cheaper mistake.

**The aggregate type is spelled here once and nowhere else.** It is the column
that separates these streams from every other context's, so a second spelling of
it is a second set of streams nothing reconciles.

**There is no lookup by payload here.** The stream id is a pure function of the
ordered pair (``blocks/domain/ids.py``), so every question this port answers is a
direct stream read: nothing scans opening events and nothing depends on a
serialized field name staying spelled the way the codec writes it. That is what
the deterministic id buys, and it is why *is this pair blocked this way round*
costs one keyed read rather than a scan.

**The version is recovered, not taken**, so this must be constructed **per
request** from the session, exactly as the event store dependency is. A pair this
repository never read has no entry and is appended at version zero — which is
also what makes two concurrent first blocks of one person collide on version 1 of
one stream rather than quietly opening a second.
"""

from __future__ import annotations

from uuid import UUID

from app.application.ports import DomainEventPublisher, DomainEventStore
from app.modules.blocks.domain.block import Block
from app.modules.blocks.domain.ids import block_id

BLOCK_AGGREGATE = "block"


class EventSourcedBlockRepository:
    """``BlockRepository`` over ``DomainEventStore``."""

    def __init__(
        self,
        *,
        event_store: DomainEventStore,
        events: DomainEventPublisher,
    ) -> None:
        self._event_store = event_store
        self._events = events
        # Aggregate id -> the stream version this request has seen. Read by
        # ``save`` as the expected version.
        self._versions: dict[UUID, int] = {}

    async def load(self, *, blocker_id: UUID, blocked_id: UUID) -> Block | None:
        stored = await self._event_store.load_stream(
            aggregate_type=BLOCK_AGGREGATE,
            aggregate_id=block_id(blocker_id, blocked_id),
        )
        if not stored:
            return None
        block = Block.from_history(record.event for record in stored)
        self._remember(block)
        return block

    async def save(self, block: Block) -> None:
        pending = block.pull_events()
        if not pending:
            return

        await self._event_store.append(
            aggregate_type=BLOCK_AGGREGATE,
            aggregate_id=block.id,
            expected_version=self._versions.get(block.id, 0),
            events=pending,
        )
        await self._events.publish_many(pending)
        # Deliberately no commit: the transaction boundary is the use case's,
        # for the reason every repository in this codebase leaves it there.
        self._remember(block)

    def _remember(self, block: Block) -> None:
        self._versions[block.id] = block.version
