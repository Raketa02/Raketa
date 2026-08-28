"""The one connection pool this process holds to the ephemeral store.

Shaped exactly like ``app/infrastructure/database/engine.py``, and for the same
reason: a pool is **per process**, opened when the application starts and closed
when it stops, and everything that wants one is handed the same object rather
than opening a second. A client built per request is a connection pool per
request, which is a connection storm dressed as dependency injection.

**Not an adapter.** Nothing here knows what a ledger is; the ledgers are in
``matchmaking/infrastructure/redis_ledgers.py`` and they are handed this client.
That is why a dependency declaration may import this module, the way it may
import ``get_db``: what it reaches for is the connection, not the thing built
over it.

**Nothing here fails.** Constructing a client opens no socket — ``redis-py``
connects lazily on the first command — so an application whose Redis is down
starts normally and its ledgers degrade, which is the posture
``matchmaking/domain/ledgers.py`` argues for at length. The refusal that *does*
exist is in the settings: an unprovisioned environment that never set
``REDIS_URL`` will not boot at all, because permanently degraded is not a state
to inherit from a laptop's service name.
"""

from __future__ import annotations

from redis.asyncio import Redis

from app.core.config import Settings

#: How long one command may take, connection included.
#:
#: **Short, and a constant rather than a setting.** Both ledgers sit inline on
#: paths a player is waiting on, and a wedged store must cost a search its spread
#: rather than its response — a fail-soft port that waits forever fails soft in
#: name only. Two seconds is far outside anything a healthy local or in-VPC Redis
#: does and far inside anything a person notices, and it is not configuration
#: because an operator raising it would be turning the posture off.
REDIS_TIMEOUT_SECONDS = 2.0


def create_redis_client(settings: Settings) -> Redis:
    """A client over ``REDIS_URL``, decoding replies to ``str``.

    ``decode_responses`` is on so the ledgers deal in strings rather than
    littering ``.decode()`` through code whose whole subject is counts and ids.
    """

    return Redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        socket_timeout=REDIS_TIMEOUT_SECONDS,
        socket_connect_timeout=REDIS_TIMEOUT_SECONDS,
    )


_client: Redis | None = None


def init_redis(settings: Settings) -> Redis:
    global _client
    _client = create_redis_client(settings)
    return _client


def get_redis() -> Redis:
    if _client is None:
        raise RuntimeError("redis not initialised — call init_redis() first")
    return _client


async def close_redis() -> None:
    global _client
    if _client is not None:
        # `type: ignore` because the obsolete `types-redis` stubs in the dev
        # group shadow redis-py's own inline types and predate `aclose` — which
        # exists, and is the spelling `close` was deprecated in favour of. The
        # ignore is here rather than the deprecated call, so the day the stubs
        # are dropped this is one line to delete rather than a call to correct.
        await _client.aclose()  # type: ignore[attr-defined]
        _client = None
