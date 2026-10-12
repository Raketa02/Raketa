"""Each event stream loaded once, for the life of one read (#704, ADR-0197 §2c).

A deck read's adapters each load what they need on their own, over one request:
a person's rating stream for the pair rule, again for the forecasts and again
for the people on the cards; their profile twice; a rescue's candidates again.
Each load is a statement and a replay. This wrapper sits over the store those
adapters share, and the first load of a stream is the load — every later one is
handed the same events, and two in flight together wait on one.

**Scoped to the read, and to a read.** It is built in the deck read's
composition and lives no longer than the request, so nothing is ever believed
past the transaction that read it (ADR-0189's 2026-09-30 amendment: the deck is
a projection, recomputed at every read and stored nowhere). It is never wired
into a use case that writes, because a write that appends and reloads in one
session must see its own events. That rule is held by composition, not by this
class — but ``append`` still forgets the stream it appended to, so a misuse
would be slower rather than wrong.

A search by first event is handed straight through: it crosses streams and is
not one, and nothing in the deck read repeats it.
"""

from __future__ import annotations

import asyncio
from collections.abc import Iterable, Mapping
from typing import final
from uuid import UUID

from app.application.events.store import StoredDomainEvent
from app.application.ports.events import DomainEventStore
from app.shared.domain import DomainEvent

Stream = tuple[str, UUID]


@final
class ReadOnceEventStore:
    """``DomainEventStore`` over another, remembering each stream it loaded."""

    def __init__(self, inner: DomainEventStore) -> None:
        self._inner = inner
        self._loads: dict[Stream, asyncio.Future[list[StoredDomainEvent]]] = {}

    async def load_stream(
        self, *, aggregate_type: str, aggregate_id: UUID
    ) -> list[StoredDomainEvent]:
        stream: Stream = (aggregate_type, aggregate_id)
        waiting = self._loads.get(stream)
        if waiting is not None:
            # A copy for each reader: a list handed out twice is a list one
            # reader can change under another.
            return list(await waiting)

        loading = asyncio.get_running_loop().create_future()
        self._loads[stream] = loading
        try:
            events = await self._inner.load_stream(
                aggregate_type=aggregate_type, aggregate_id=aggregate_id
            )
        except BaseException as exc:
            # A failure is not an answer: the stream is forgotten so the next
            # reader asks the store, and whoever waited on this load is told.
            self._loads.pop(stream, None)
            if isinstance(exc, asyncio.CancelledError):
                loading.cancel()
            else:
                loading.set_exception(exc)
                # Retrieved here, so a load nobody else waited on is not an
                # "exception was never retrieved" at collection: the raise
                # below is how this reader hears of it.
                loading.exception()
            raise
        loading.set_result(events)
        return list(events)

    async def append(
        self,
        *,
        aggregate_type: str,
        aggregate_id: UUID,
        expected_version: int,
        events: Iterable[DomainEvent],
    ) -> list[StoredDomainEvent]:
        appended = await self._inner.append(
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            expected_version=expected_version,
            events=events,
        )
        self._loads.pop((aggregate_type, aggregate_id), None)
        return appended

    async def find_aggregate_ids_by_first_event(
        self, *, aggregate_type: str, payload_equals: Mapping[str, str]
    ) -> list[UUID]:
        return await self._inner.find_aggregate_ids_by_first_event(
            aggregate_type=aggregate_type, payload_equals=payload_equals
        )


__all__ = ["ReadOnceEventStore"]
