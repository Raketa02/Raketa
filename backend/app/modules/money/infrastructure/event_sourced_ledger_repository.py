"""The Ledger repository, over the event store.

What it owns is what a repository over an event store always owns: the
aggregate-type string the streams are filed under, the replay, the version the
next append expects, and how the whole set is found.

**Roughly a dozen lines here read like ``EventSourcedSkillRatingRepository``,
and that is deliberate.** ADR-0018 declined a generic event-sourced base because
event-sourced-versus-persisted-with-events is a per-context decision that has to
stay open — and five contexts have now made it, three of them the other way. A
third concrete adapter that reads straight through is the cheaper mistake.

**There is no table.** Money adds no migration and no ORM model: a ledger *is*
its stream, and the only cross-stream read it needs is a scan the store already
answers. A projection is what ADR-0018's escape hatch is for, on the day tens of
rows becomes thousands — and building it now would be a cache in front of a
query nobody has measured.

**A player with no movements has no stream**, so ``load`` hands back an empty
ledger rather than nothing. The version it remembers is zero, which is exactly
what *"this stream does not exist yet"* means to the store.
"""

from __future__ import annotations

from uuid import UUID

from app.application.ports import DomainEventPublisher, DomainEventStore
from app.modules.money.domain.ids import ledger_stream_id
from app.modules.money.domain.ledger import Ledger

LEDGER_AGGREGATE = "ledger"


class EventSourcedLedgerRepository:
    """``LedgerRepository`` over ``DomainEventStore``."""

    def __init__(
        self,
        *,
        event_store: DomainEventStore,
        events: DomainEventPublisher,
    ) -> None:
        self._event_store = event_store
        self._events = events
        # Aggregate id -> the stream version this request has seen. Read by
        # `save` as the expected version, which is what makes a second writer
        # lose rather than interleave.
        self._versions: dict[UUID, int] = {}

    async def load(self, player_id: UUID) -> Ledger:
        stream_id = ledger_stream_id(player_id)
        stored = await self._event_store.load_stream(
            aggregate_type=LEDGER_AGGREGATE,
            aggregate_id=stream_id,
        )
        ledger = (
            Ledger.for_player(player_id)
            if not stored
            else Ledger.from_history(record.event for record in stored)
        )
        self._remember(ledger)
        return ledger

    async def save(self, ledger: Ledger) -> None:
        pending = ledger.pull_events()
        if not pending:
            return

        await self._event_store.append(
            aggregate_type=LEDGER_AGGREGATE,
            aggregate_id=ledger.id,
            expected_version=self._versions.get(ledger.id, 0),
            events=pending,
        )
        await self._events.publish_many(pending)
        # Deliberately no commit: a seat payment writes the seat, the
        # reservation and this movement in one transaction, and that boundary
        # belongs to the use case (`Raketa02/Raketa#70`).
        self._remember(ledger)

    async def all_ledgers(self) -> list[Ledger]:
        # Every stream of this type, found through the opening-event index with
        # nothing to match on — which is the store's own spelling of *all of
        # them*, oldest stream first.
        ledger_ids = await self._event_store.find_aggregate_ids_by_first_event(
            aggregate_type=LEDGER_AGGREGATE,
            payload_equals={},
        )

        ledgers: list[Ledger] = []
        for ledger_id in ledger_ids:
            stored = await self._event_store.load_stream(
                aggregate_type=LEDGER_AGGREGATE,
                aggregate_id=ledger_id,
            )
            if not stored:
                continue
            ledger = Ledger.from_history(record.event for record in stored)
            # Registered like any read aggregate, so one that was found is one
            # that can be saved. The reconciliation never does — it is built
            # without a unit of work — but the scan is not only its.
            self._remember(ledger)
            ledgers.append(ledger)
        return ledgers

    def _remember(self, ledger: Ledger) -> None:
        self._versions[ledger.id] = ledger.version
