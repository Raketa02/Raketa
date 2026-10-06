"""The HTTP suite runs against no sidecar, and that is a claim worth asserting.

The API seam is an ASGI transport over an in-memory SQLite database. No MinIO,
no CLIP container, and — since the ephemeral store arrived — no Redis. That is
the acceptance criterion rather than a convenience: a suite that only passes
with containers up is a suite CI cannot be trusted to run.

**The ephemeral store gets tests of its own** rather than being left to the
fixtures, because a room's live channel is the one reader of it left (#579) and
it runs over a fake the suite overrides: a request path that quietly grew its
own client would pass every other test and fail on a laptop with no Redis.
"""

from __future__ import annotations

import pytest

from app.infrastructure.redis_client import get_redis
from app.main import create_app


async def test_serving_a_request_opens_no_connection_pool(client):
    """Building the application and serving from it reaches for no store.

    The lifespan is what opens the pool, and the test transport does not run
    one — so this is the assertion that the *request* path has not quietly grown
    its own client on the side. `get_redis` raising is the public spelling of
    *this process has no pool*.
    """

    response = await client.get("/health")

    assert response.status_code == 200
    with pytest.raises(RuntimeError, match="not initialised"):
        get_redis()


def test_the_application_starts_with_no_ephemeral_store_reachable():
    """Constructing the app touches no store, and constructing a client would
    connect to nothing anyway.

    It is the same property the live channel's fail-soft posture rests on, one
    layer down: a store that is down costs liveness, never a start.
    """

    create_app()

    with pytest.raises(RuntimeError, match="not initialised"):
        get_redis()
