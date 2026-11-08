"""The kept General orders every test reads through — **the in-memory
equivalent** of the ephemeral store's, one per test database (#770).

**One per database, because the store is the deployment's**: an API process's
requests and its outbox worker read and forget one Redis, so the application a
test drives (the ``general_orders`` fixture, overridden on ``app``) and the
outbox a test drains (``players_world.deliver_the_outbox``) share one here —
a ranking write forgets the order the next request would have read. Keyed by
the test's session factory, which is the test's database, and let go with it.
"""

from __future__ import annotations

from weakref import WeakKeyDictionary

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.modules.rankings.infrastructure.in_memory_general_orders import (
    InMemoryGeneralOrders,
)

_KEPT: WeakKeyDictionary[async_sessionmaker[AsyncSession], InMemoryGeneralOrders] = (
    WeakKeyDictionary()
)


def kept_orders_of(
    session_factory: async_sessionmaker[AsyncSession],
) -> InMemoryGeneralOrders:
    """The orders kept beside this database."""

    kept = _KEPT.get(session_factory)
    if kept is None:
        kept = _KEPT[session_factory] = InMemoryGeneralOrders()
    return kept
