"""How this process connects to the ephemeral store.

**One pool, shared.** Shaped exactly like
``app/infrastructure/database/engine.py``, and for the same reason: a pool is
**per process**, opened when the application starts and closed when it stops,
and everything that wants one is handed the same object rather than opening a
second. A client built per request is a connection pool per request, which is a
connection storm dressed as dependency injection.

**And one exception, which is why there are two factories below.** A connect
timeout and a read timeout are two different things (`#342
<https://github.com/Raketa02/Raketa/issues/342>`_), and a **subscriber** wants
one of them and emphatically not the other. It gets its own client rather than a
flag on the shared one: a blocking read has no business in the pool a player's
critical path draws its commands from, and that is a decision to take once here
rather than to re-open at every call site.

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

#: How long **opening a connection** may take, on any client this module builds.
#:
#: A store that is not accepting connections has to be found out about rather
#: than waited on: the ledgers behind this fail soft, and a fail-soft port that
#: waits forever fails soft in name only. Two seconds is far outside anything a
#: healthy local or in-VPC Redis does and far inside anything a person notices.
#: **A subscriber shares this half**, because *cannot connect* is a fault on a
#: long-lived subscription exactly as it is on a command.
#:
#: A constant rather than a setting: an operator raising it would be turning the
#: posture off.
REDIS_CONNECT_TIMEOUT_SECONDS = 2.0

#: How long a **command may wait for its reply**, once connected.
#:
#: Same number as the connect timeout, for a different reason, which is the whole
#: argument for two names. Both ledgers sit inline on paths a player is waiting
#: on, and a wedged store must cost a search its spread rather than its response.
#:
#: **This is a request/response deadline and only that.** It has nothing to say
#: about a subscription, where waiting *is* the operation — see
#: ``create_redis_subscriber_client``. Also a constant rather than a setting, and
#: for the same reason as the connect timeout.
REDIS_READ_TIMEOUT_SECONDS = 2.0


def _build_client(settings: Settings, *, read_timeout: float | None) -> Redis:
    """The one place a client is constructed, so the two below cannot drift.

    Everything except the read deadline is the same on both by construction
    rather than by two authors remembering to keep them in step —
    ``decode_responses`` above all, which the ledgers' whole vocabulary of
    counts and ids depends on. The read timeout is the parameter because it is
    the one thing the two clients are *for*: bounded on a command, absent on a
    subscription.

    Private, and deliberately. The public names are the two callers below,
    because *which client am I asking for* is a question with two answers and
    not a float somebody passes.
    """

    return Redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        socket_timeout=read_timeout,
        socket_connect_timeout=REDIS_CONNECT_TIMEOUT_SECONDS,
    )


def create_redis_client(settings: Settings) -> Redis:
    """A client over ``REDIS_URL``, **bounded at both ends**.

    This is the one ``init_redis`` holds for the process and the one every
    command path is handed.
    """

    return _build_client(settings, read_timeout=REDIS_READ_TIMEOUT_SECONDS)


def create_redis_subscriber_client(settings: Settings) -> Redis:
    """The same client with **no read deadline**, for a long-lived subscription.

    A subscriber is idle by design, and on ``redis-py`` 7.4 a ``socket_timeout``
    turns that idleness into a fault. ``PubSub.listen()`` calls
    ``parse_response(block=True)``, which passes ``timeout=None`` down, and
    ``Connection.read_response`` reads that as *use the socket's* rather than as
    *do not time out* — ``read_timeout = timeout if timeout is not None else
    self.socket_timeout``. So a subscription built on the request/response
    client above times out every ``REDIS_READ_TIMEOUT_SECONDS``.

    **And it does not merely reconnect — it raises.** ``PubSub`` wraps that read
    in ``call_with_retry``, whose failure callback reconnects and resubscribes;
    but a connection's default ``Retry`` here allows **zero** retries, so
    ``failures (1) > retries (0)`` and the ``TimeoutError`` is re-raised at the
    caller. An idle ``async for`` over ``listen()`` therefore dies every two
    seconds rather than looping quietly, and **whatever was published in the gap
    is gone** either way, since pub/sub replays nothing to a channel nobody was
    on. That is #342, and the fix is not a dependency bump: the deadline simply
    does not belong here.

    **Connecting is still bounded** — see ``REDIS_CONNECT_TIMEOUT_SECONDS``. The
    half that drops away is the one that was measuring the wrong thing.

    **The cost of dropping it is real and is not this factory's to pay.** A read
    deadline is also the crude thing that noticed a connection which had died
    without saying so. Liveness on a subscription is the *subscriber's* to keep;
    ADR-0147's amendment names the ways and leaves the choice to whoever builds
    the first one.

    **The caller owns both ends of this one.** It is deliberately not the
    process's pool: this module's opening paragraph is about the client every
    command path shares, and a blocking read has no business in it. Whoever opens
    one closes it, the way ``app/seeds/paths.py`` does with the client it opens
    for a command that has no lifespan to hang it on.
    """

    return _build_client(settings, read_timeout=None)


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
