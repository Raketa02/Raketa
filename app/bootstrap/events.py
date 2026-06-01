from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.events import (
    EventDispatcher,
    EventCatalog,
)
from app.application.events.deliver_event_batch import EventBatch
from app.core.config import Settings
from app.infrastructure.events.event_delivery_worker import (
    EventWorker,
)
from app.infrastructure.events.json_event_codec import JsonEventCodec
from app.infrastructure.events.sqlalchemy_domain_event_store import (
    SqlAlchemyEventStore,
)
from app.infrastructure.events.sqlalchemy_event_delivery_queue import (
    SqlAlchemyOutboxRepository,
)
from app.infrastructure.events.transactional_publisher import (
    EventPublisher,
)
from app.modules.auth.application.event_subscriptions import (
    register_auth_events,
    subscribe_auth_handlers,
)
from app.modules.users.application.event_subscriptions import (
    register_user_events,
    subscribe_user_handlers,
)
from app.shared.clock import Clock, SystemClock


@dataclass(frozen=True)
class EventRuntime:
    codec: JsonEventCodec
    dispatcher: EventDispatcher

    def create_publisher_for(self, *, session: AsyncSession) -> EventPublisher:
        return EventPublisher(
            outbox=SqlAlchemyOutboxRepository(session), codec=self.codec
        )

    def create_domain_event_store_for(
        self, *, session: AsyncSession
    ) -> SqlAlchemyEventStore:
        return SqlAlchemyEventStore(session, self.codec)

    def create_event_batch_for(
        self,
        *,
        session: AsyncSession,
        clock: Clock,
        batch_size: int,
    ) -> EventBatch:
        return EventBatch(
            outbox=SqlAlchemyOutboxRepository(session),
            codec=self.codec,
            dispatcher=self.dispatcher,
            clock=clock,
            batch_size=batch_size,
        )


def build_event_runtime() -> EventRuntime:
    catalog = EventCatalog()
    register_user_events(catalog)
    register_auth_events(catalog)

    dispatcher = EventDispatcher()
    subscribe_user_handlers(dispatcher)
    subscribe_auth_handlers(dispatcher)

    return EventRuntime(
        codec=JsonEventCodec(catalog),
        dispatcher=dispatcher,
    )


def build_event_delivery_worker(
    *,
    event_runtime: EventRuntime,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
    clock: Clock | None = None,
) -> EventWorker:
    processing_clock = clock or SystemClock()
    return EventWorker(
        session_factory=session_factory,
        batch_factory=lambda session: event_runtime.create_event_batch_for(
            session=session,
            clock=processing_clock,
            batch_size=settings.EVENT_DELIVERY_BATCH_SIZE,
        ),
        poll_interval_seconds=settings.EVENT_DELIVERY_POLL_INTERVAL_SECONDS,
    )
