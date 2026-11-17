"""When each player last closed *Needs your answer*: one stream per player,
filed under their own id (#815; ``docs/adr/0205`` §3).

The same shape as the other aggregate repositories — the aggregate type spelled
once, state rebuilt by replay, the version remembered from the load and expected
by the append (``docs/adr/0018``). **``load`` answers no watermark for a stream
never written**: a player who never closed the sheet has seen nothing yet.

**No projection**, as Games & money has none: Home reads one player's
watermark, and a stream read is one query. The stream grows only when the
watermark moves, which only a newer arrival can make it do.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.application.ports import DomainEventPublisher, DomainEventStore
from app.modules.proposals.domain.needs_your_answer import NeedsYourAnswerVisit

NEEDS_YOUR_ANSWER_AGGREGATE = "needs_your_answer_visit"


@final
class EventSourcedNeedsYourAnswerVisits:
    """``NeedsYourAnswerVisits`` over ``DomainEventStore``."""

    def __init__(
        self, *, event_store: DomainEventStore, events: DomainEventPublisher
    ) -> None:
        self._event_store = event_store
        self._events = events
        self._versions: dict[UUID, int] = {}

    async def load(self, player_id: UUID) -> NeedsYourAnswerVisit:
        stored = await self._event_store.load_stream(
            aggregate_type=NEEDS_YOUR_ANSWER_AGGREGATE, aggregate_id=player_id
        )
        visit = NeedsYourAnswerVisit.from_history(
            player_id, (record.event for record in stored)
        )
        self._versions[player_id] = visit.version
        return visit

    async def save(self, visit: NeedsYourAnswerVisit) -> None:
        pending = visit.pull_events()
        if not pending:
            return
        await self._event_store.append(
            aggregate_type=NEEDS_YOUR_ANSWER_AGGREGATE,
            aggregate_id=visit.player_id,
            expected_version=self._versions.get(visit.player_id, 0),
            events=pending,
        )
        await self._events.publish_many(pending)
        # Deliberately no commit: the transaction boundary is the use case's.
        self._versions[visit.player_id] = visit.version
