"""The new bookings summary repository: one stream per club per day, and no
projection — a summary is looked up by its id, which is the club and the day
(#548)."""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.application.ports import DomainEventPublisher, DomainEventStore
from app.modules.bookings.domain.summary import NewBookingsSummary

NEW_BOOKINGS_SUMMARY_AGGREGATE = "new_bookings_summary"


@final
class EventSourcedSummaryRepository:
    """``SummaryRepository`` over ``DomainEventStore``."""

    def __init__(
        self, *, event_store: DomainEventStore, events: DomainEventPublisher
    ) -> None:
        self._event_store = event_store
        self._events = events

    async def load(self, summary_id: UUID) -> NewBookingsSummary | None:
        stored = await self._event_store.load_stream(
            aggregate_type=NEW_BOOKINGS_SUMMARY_AGGREGATE, aggregate_id=summary_id
        )
        if not stored:
            return None
        return NewBookingsSummary.from_history(record.event for record in stored)

    async def save(self, summary: NewBookingsSummary) -> None:
        pending = summary.pull_events()
        if not pending:
            return
        # Born once: a second summary of the same club and day collides here.
        await self._event_store.append(
            aggregate_type=NEW_BOOKINGS_SUMMARY_AGGREGATE,
            aggregate_id=summary.summary_id,
            expected_version=0,
            events=pending,
        )
        await self._events.publish_many(pending)
        # Deliberately no commit: the transaction boundary is the use case's.
