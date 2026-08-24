from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.events import (
    EventDispatcher,
    EventCatalog,
)
from app.application.events.deliver_event_batch import EventBatch
from app.core.config import Settings
from app.infrastructure.clock import SystemClock
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
from app.modules.now.domain.ports import ScoringContexts
from app.infrastructure.events.transactional_publisher import (
    EventPublisher,
)
from app.kernel import Clock
from app.modules.auth.application.event_subscriptions import (
    register_auth_events,
    subscribe_auth_handlers,
)
from app.modules.matches.application.event_subscriptions import (
    register_match_events,
    subscribe_match_handlers,
)
from app.modules.money.application.event_subscriptions import (
    register_money_events,
    subscribe_money_handlers,
)
from app.modules.rating.application.event_subscriptions import (
    register_rating_events,
    subscribe_rating_handlers,
)
from app.modules.users.application.event_subscriptions import (
    register_user_events,
    subscribe_user_handlers,
)


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
    register_rating_events(catalog)
    register_match_events(catalog)
    register_money_events(catalog)

    dispatcher = EventDispatcher()
    subscribe_user_handlers(dispatcher)
    subscribe_auth_handlers(dispatcher)
    subscribe_rating_handlers(dispatcher)
    subscribe_match_handlers(dispatcher)
    subscribe_money_handlers(dispatcher)

    return EventRuntime(
        codec=JsonEventCodec(catalog),
        dispatcher=dispatcher,
    )


@lru_cache(maxsize=1)
def get_event_runtime() -> EventRuntime:
    """The process's event runtime, built once and reachable from anywhere.

    It used to be reachable only as `request.app.state.event_runtime`, which
    made the domain-event machinery a property of a *served HTTP request* rather
    than of the process — so a seed run or a management command could only get
    one by booting the API or by building a second, parallel runtime.

    Cached, and safe to cache, because `EventRuntime` is frozen and what it
    holds is declarative: a catalog of event names and a table of handler
    subscriptions, both registered from static code. Nothing about it varies per
    request, and nothing mutates it after `build_event_runtime` returns.
    `build_event_runtime` stays public and uncached for the callers that
    genuinely want a fresh one — a test asserting on a codec in isolation.

    Cached the same way `get_settings` is, and with the same escape hatch:
    `get_event_runtime.cache_clear()`.
    """
    return build_event_runtime()


def build_event_delivery_worker(
    *,
    event_runtime: EventRuntime,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
    scoring_contexts: ScoringContexts,
    clock: Clock | None = None,
) -> EventWorker:
    # Imported here rather than at the top because `composition` imports this
    # module for `EventRuntime`, and the cycle is real: the composition root has
    # to know how to build an event publisher, and the worker has to know how to
    # build a use case. One deferred import at the one call site is cheaper than
    # a third bootstrap module holding two functions.
    from app.bootstrap.composition import (
        build_cascade_tick,
        build_match_wake_batch,
    )

    processing_clock = clock or SystemClock()
    return EventWorker(
        session_factory=session_factory,
        batch_factory=lambda session: event_runtime.create_event_batch_for(
            session=session,
            clock=processing_clock,
            batch_size=settings.EVENT_DELIVERY_BATCH_SIZE,
        ),
        # ADR-0076's second lookup, on the tick the outbox already runs.
        wake_batch_factory=lambda session: build_match_wake_batch(
            session=session,
            event_runtime=event_runtime,
            clock=processing_clock,
        ),
        # ADR-0061's two dispatch jobs, on the same tick. Last of the three,
        # because the two above it decide what is *true* and this one decides
        # who is *told*.
        cascade_batch_factory=lambda session: build_cascade_tick(
            session=session,
            event_runtime=event_runtime,
            contexts=scoring_contexts,
            clock=processing_clock,
        ),
        poll_interval_seconds=settings.EVENT_DELIVERY_POLL_INTERVAL_SECONDS,
    )
