"""The HTTP suite runs against no sidecar, and that is a claim worth asserting.

The API seam is an ASGI transport over an in-memory SQLite database. No MinIO,
no CLIP container, and — since the ephemeral store arrived — no Redis. That is
the acceptance criterion rather than a convenience: a suite that only passes
with containers up is a suite CI cannot be trusted to run.

**The ledger is the worst of the three to get wrong**, which is why it gets a
test of its own rather than being left to the fixtures. A missing object store
fails a request and a missing sidecar fails a review; a missing ledger answers
*nobody has been shown to anybody* and *nothing is suppressed*, which are
perfectly plausible answers. A suite quietly talking to no Redis at all would
be green and would prove nothing.
"""

from __future__ import annotations

import pytest

from app.infrastructure.redis_client import get_redis
from app.main import create_app
from tests.unit.fake_ledgers import InMemoryExposureLedger, InMemorySuppressionLedger


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

    It is the same property the ledgers' fail-soft posture rests on, one layer
    down: a store that is down costs answers, never a start.
    """

    create_app()

    with pytest.raises(RuntimeError, match="not initialised"):
        get_redis()


async def test_both_ledgers_are_the_in_memory_ones(
    client, exposure_ledger, suppression_ledger
):
    """The fixtures the whole suite runs against, named.

    Asserted rather than assumed because the override is invisible: a route
    added tomorrow that reached `get_redis` directly instead of asking for the
    port would pass every other test in this file and fail on a laptop with no
    Redis.
    """

    assert isinstance(exposure_ledger, InMemoryExposureLedger)
    assert isinstance(suppression_ledger, InMemorySuppressionLedger)
