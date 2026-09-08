"""A connect timeout and a read timeout are two different things.

One constant used to be both (`#342
<https://github.com/Raketa02/Raketa/issues/342>`_), which made the shared client
unusable by a long-lived subscriber: ``pubsub.listen()`` passes no timeout of its
own, ``read_response`` falls back to the socket's, and an idle subscription
therefore raises every two seconds and loses whatever was published while it
reconnected. Nothing subscribes today, so nothing was broken today — these tests
exist so the first subscriber does not inherit it silently.

**The re-merge is the failure mode worth guarding, and it is invisible at rest.**
Both constants hold ``2.0``, so a client built from one where the other was meant
looks exactly right in ``connection_kwargs``. Only a substitution can tell them
apart, which is why the last two tests move one constant and assert the other
did not follow.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from redis.asyncio import Redis

import app.infrastructure.redis_client as redis_client
from app.core.config import Settings
from app.infrastructure.redis_client import (
    REDIS_CONNECT_TIMEOUT_SECONDS,
    REDIS_READ_TIMEOUT_SECONDS,
    create_redis_client,
    create_redis_subscriber_client,
)


def _settings(**overrides) -> Settings:
    """Built rather than read from ``get_settings()``, on ``test_lifespan.py``'s
    precedent: that one is ``lru_cache``d and cleared only inside the HTTP
    ``client`` fixture, so reading it here would make these tests depend on
    ambient process state they never set.
    """

    return Settings(WRITER_DB_URL="sqlite+aiosqlite:///:memory:", **overrides)


async def _connection_kwargs(build: Callable[[Settings], Redis]) -> dict[str, Any]:
    """Build a client, read what its pool was built with, and close it again.

    Closed rather than dropped even though constructing one opens no socket, on
    the rule the module under test states in its own voice: *whoever opens one
    closes it*. A test that took the exemption would be the first reader to
    learn the rule and the first to ignore it.

    ``type: ignore`` for the same reason ``redis_client.py`` carries one — the
    obsolete ``types-redis`` stubs predate ``aclose``.
    """

    client = build(_settings())
    try:
        return dict(client.connection_pool.connection_kwargs)
    finally:
        await client.aclose()  # type: ignore[attr-defined]


async def test_the_request_response_client_bounds_both_the_connect_and_the_read():
    """Today's behaviour, unchanged. The ledgers sit inline on paths a player is
    waiting on, so a wedged store must cost a search its spread and not its
    response — which needs *both* halves bounded.
    """

    kwargs = await _connection_kwargs(create_redis_client)

    assert kwargs["socket_connect_timeout"] == REDIS_CONNECT_TIMEOUT_SECONDS
    assert kwargs["socket_timeout"] == REDIS_READ_TIMEOUT_SECONDS


async def test_a_subscriber_loses_the_read_deadline_and_keeps_the_connect_one():
    """The whole point of the split, and both halves are one claim about one
    client. A subscription is idle by design and idle is not a fault, so there is
    no read deadline to enforce on one — while a store that accepts no connection
    must still be found out about rather than waited on for ever.
    """

    kwargs = await _connection_kwargs(create_redis_subscriber_client)

    # Indexed rather than ``.get()``: the key is present and holds ``None``, and
    # a ``.get()`` would pass just as happily if it vanished altogether.
    assert kwargs["socket_timeout"] is None
    assert kwargs["socket_connect_timeout"] == REDIS_CONNECT_TIMEOUT_SECONDS


async def test_the_subscriber_client_differs_in_the_read_timeout_and_nothing_else():
    """A second client is a second chance to drift. ``decode_responses``, the URL
    and everything else the pool was built with are the same object's; the read
    deadline is the one deliberate difference.
    """

    request_response = await _connection_kwargs(create_redis_client)
    subscriber = await _connection_kwargs(create_redis_subscriber_client)

    def without_the_read_timeout(kwargs: dict[str, Any]) -> dict[str, Any]:
        return {k: v for k, v in kwargs.items() if k != "socket_timeout"}

    assert without_the_read_timeout(subscriber) == without_the_read_timeout(
        request_response
    )


async def test_the_read_timeout_is_its_own_constant(monkeypatch):
    """Substituted, because both constants hold the same number.

    Move the read timeout and the connect timeout must not move with it. A later
    edit that folded the two back into one name would fail here rather than
    silently re-arming #342 for whoever subscribes next.
    """

    monkeypatch.setattr(redis_client, "REDIS_READ_TIMEOUT_SECONDS", 9.0)

    kwargs = await _connection_kwargs(create_redis_client)

    assert kwargs["socket_timeout"] == 9.0
    assert kwargs["socket_connect_timeout"] == REDIS_CONNECT_TIMEOUT_SECONDS


async def test_the_connect_timeout_is_its_own_constant(monkeypatch):
    """The mirror, and the half a subscriber shares. Moving the connect timeout
    moves it on both clients and leaves neither read deadline behind it.
    """

    monkeypatch.setattr(redis_client, "REDIS_CONNECT_TIMEOUT_SECONDS", 9.0)

    request_response = await _connection_kwargs(create_redis_client)
    subscriber = await _connection_kwargs(create_redis_subscriber_client)

    assert request_response["socket_connect_timeout"] == 9.0
    assert subscriber["socket_connect_timeout"] == 9.0
    assert request_response["socket_timeout"] == REDIS_READ_TIMEOUT_SECONDS
    assert subscriber["socket_timeout"] is None


# ---------------------------------------------------------------------------
# The process's two clients
# ---------------------------------------------------------------------------


async def test_the_two_process_clients_are_two_clients():
    """One pool for commands and one for subscriptions, and they differ.

    #342's whole finding, applied: a subscription built on the command client
    raises every two seconds and loses whatever was published while it
    reconnected. The two are told apart by the read deadline, and by nothing
    else — which is exactly why *are these the same object* is worth asserting
    rather than assuming from two initialisers with different names.
    """

    settings = _settings()
    try:
        commands = redis_client.init_redis(settings)
        subscriptions = redis_client.init_redis_subscriber(settings)

        assert commands is not subscriptions
        assert redis_client.get_redis() is commands
        assert redis_client.get_redis_subscriber() is subscriptions
        assert (
            subscriptions.connection_pool.connection_kwargs.get("socket_timeout")
            is None
        )
    finally:
        await redis_client.close_redis()
        await redis_client.close_redis_subscriber()


async def test_a_subscriber_client_that_was_never_opened_refuses_rather_than_leaks():
    """The same refusal `get_redis` makes, and for the same reason.

    A process that never opened one has a bug, and the honest answer is a raise
    at the seam rather than a `None` that reaches a subscription and looks like
    a store that is down.
    """

    await redis_client.close_redis_subscriber()

    try:
        redis_client.get_redis_subscriber()
    except RuntimeError as exc:
        assert "subscriber" in str(exc)
    else:
        raise AssertionError("a subscriber client that was never opened must refuse")
