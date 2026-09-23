"""A small in-process Redis, so the ledger adapters are actually tested.

**Not a second implementation of the ports** — that is what
`tests/unit/fake_ledgers.py` is, and the two are different things. This is a
stand-in for the *server*, so that `RedisExposureLedger` and
`RedisSuppressionLedger` — the classes that decide the key shapes, the field
encoding and the TTLs — run inside the same contract suite as everything else
rather than being the one implementation nothing exercises. A suite that only
passes with a container up is a suite CI cannot be trusted to run, and the
alternative to this file is not *a better test*, it is *no test of the adapters
at all*.

**A deliberate subset, and it stays one.** It implements exactly the commands
the adapters issue and nothing more, so a new command in an adapter is an
`AttributeError` here rather than a silent divergence. The semantics it does
model are four: **expiry**, against a clock a test moves rather than the host's;
**`HINCRBY` creating the field it increments**; **`SADD` creating the set it adds
to**; and **pub/sub delivering only to whoever is subscribed at the moment of the
publish**, which is at-most-once and is exactly what makes a dropped frame a
thing a test can drive.

Expiry is the one a presence test drives directly (`docs/adr/0156`): a typing
heartbeat is cleared by nothing but its key running out, so *the app was killed*
is spelled here as `advance` and asserted rather than waited for.

What it deliberately does not model is everything else Redis does. It is not a
proof the adapters work against a real server; `make up` is where that is
answered. It is a proof that they build the keys they claim to and expire what
they claim to expire.
"""

from __future__ import annotations

import asyncio
from typing import Any, AsyncIterator, Iterable


class FakeRedisError(RuntimeError):
    """What a broken fake raises. Stands for any connection-level failure."""


class FakeRedis:
    """The commands the ledgers issue, over a dict and a clock."""

    def __init__(self, *, now: float = 0.0) -> None:
        self._values: dict[str, Any] = {}
        self._expires_at: dict[str, float] = {}
        self._now = now
        #: Every live subscription, by channel. A list rather than a set because
        #: two streams may follow one room, which is the ordinary case.
        self._channels: dict[str, list["FakePubSub"]] = {}
        #: What has been published, in order, for a test that wants to assert a
        #: nudge went out without standing up a subscriber to catch it.
        self.published: list[tuple[str, str]] = []

    # -- what a test drives ------------------------------------------------

    def advance(self, seconds: float) -> None:
        """Move the clock. Expiry is evaluated lazily, exactly as Redis does."""

        self._now += seconds

    def keys_held(self) -> frozenset[str]:
        """Every key that has not expired — what a test asserts key shapes on."""

        return frozenset(key for key in list(self._values) if self._live(key))

    def ttl_of(self, key: str) -> float | None:
        """Seconds left on a key, or ``None`` if it holds none."""

        if not self._live(key) or key not in self._expires_at:
            return None
        return self._expires_at[key] - self._now

    # -- the commands ------------------------------------------------------

    async def hincrby(self, name: str, key: str, amount: int = 1) -> int:
        hash_ = self._hash(name)
        # Through ``int`` on the way in, because a hash holds text and Redis
        # increments what it can parse — the exposure ledger's fields and the
        # prompt ledger's live in the same shape here as they do there.
        hash_[key] = int(hash_.get(key, 0)) + amount
        return hash_[key]

    async def hset(self, name: str, key: str, value: Any) -> int:
        hash_ = self._hash(name)
        existed = key in hash_
        hash_[key] = str(value)
        return 0 if existed else 1

    async def hmget(self, name: str, keys: Iterable[str]) -> list[str | None]:
        hash_ = self._read_hash(name)
        return [None if key not in hash_ else str(hash_[key]) for key in keys]

    async def hgetall(self, name: str) -> dict[str, str]:
        return {key: str(value) for key, value in self._read_hash(name).items()}

    async def sadd(self, name: str, *values: Any) -> int:
        members = self._set(name)
        added = 0
        for value in values:
            if str(value) not in members:
                members.add(str(value))
                added += 1
        return added

    async def smembers(self, name: str) -> set[str]:
        return set(self._values[name]) if self._live(name) else set()

    async def expire(self, name: str, seconds: int) -> bool:
        if not self._live(name):
            return False
        self._expires_at[name] = self._now + seconds
        return True

    async def set(self, name: str, value: Any, ex: int | None = None) -> bool:
        self._values[name] = str(value)
        self._expires_at.pop(name, None)
        if ex is not None:
            self._expires_at[name] = self._now + ex
        return True

    async def get(self, name: str) -> str | None:
        return self._values.get(name) if self._live(name) else None

    async def mget(self, keys: Iterable[str]) -> list[str | None]:
        return [self._values.get(key) if self._live(key) else None for key in keys]

    async def publish(self, channel: str, message: Any) -> int:
        """Deliver to whoever is on the channel **right now**, and count them.

        **Nothing is retained.** A publish to a channel nobody is on is delivered
        to nobody and is gone, which is real Redis pub/sub and is the property
        the live channel is designed around: a missed nudge costs latency, and
        the next one repairs it.
        """

        self.published.append((channel, str(message)))
        listeners = self._channels.get(channel, ())
        for listener in listeners:
            listener.deliver(channel, str(message))
        return len(listeners)

    def pubsub(self) -> "FakePubSub":
        return FakePubSub(self)

    # -- what the subscriptions do to this client --------------------------

    def _subscribe(self, pubsub: "FakePubSub", channel: str) -> None:
        self._channels.setdefault(channel, []).append(pubsub)

    def _unsubscribe(self, pubsub: "FakePubSub") -> None:
        for channel, listeners in list(self._channels.items()):
            if pubsub in listeners:
                listeners.remove(pubsub)
            if not listeners:
                del self._channels[channel]

    def subscribers_on(self, channel: str) -> int:
        """How many streams are following this channel. What a test asserts an
        unsubscribe with, since a leaked subscription is otherwise invisible."""

        return len(self._channels.get(channel, ()))

    def pipeline(self, transaction: bool = True) -> "FakePipeline":
        return FakePipeline(self)

    async def aclose(self) -> None:
        return None

    # -- internals ---------------------------------------------------------

    def _live(self, key: str) -> bool:
        expires_at = self._expires_at.get(key)
        if expires_at is not None and expires_at <= self._now:
            self._values.pop(key, None)
            self._expires_at.pop(key, None)
            return False
        return key in self._values

    def _set(self, name: str) -> set[str]:
        if not self._live(name):
            self._values[name] = set()
        return self._values[name]

    def _hash(self, name: str) -> dict[str, Any]:
        if not self._live(name):
            self._values[name] = {}
        return self._values[name]

    def _read_hash(self, name: str) -> dict[str, Any]:
        return self._values[name] if self._live(name) else {}


class FakePubSub:
    """One subscription, over an ``asyncio.Queue``.

    Mirrors the one piece of `redis.asyncio`'s ``PubSub`` the adapter depends on:
    ``listen()`` is an infinite async iterator that yields the subscribe
    confirmation first and then every message, and blocks in between. A
    subscriber that stopped iterating between two publishes would miss the
    second in real Redis too — the queue is what a delivered-while-listening
    message goes into, and nothing is retained for a channel nobody is on.
    """

    def __init__(self, client: FakeRedis) -> None:
        self._client = client
        self._inbox: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._closed = False

    async def subscribe(self, channel: str) -> None:
        self._client._subscribe(self, channel)
        await self._inbox.put({"type": "subscribe", "channel": channel, "data": 1})

    def deliver(self, channel: str, message: str) -> None:
        self._inbox.put_nowait({"type": "message", "channel": channel, "data": message})

    async def listen(self) -> AsyncIterator[dict[str, Any]]:
        while not self._closed:
            yield await self._inbox.get()

    async def aclose(self) -> None:
        self._closed = True
        self._client._unsubscribe(self)


class FakePipeline:
    """Queues commands and applies them on ``execute``.

    Mirrors `redis.asyncio`'s shape, where queuing is **not** awaited and only
    ``execute`` is — which is the one piece of that API an adapter can get
    wrong in a way nothing else would notice.
    """

    def __init__(self, client: FakeRedis) -> None:
        self._client = client
        self._queued: list[tuple[str, tuple, dict]] = []

    async def __aenter__(self) -> "FakePipeline":
        return self

    async def __aexit__(self, *exc_info: Any) -> None:
        return None

    def hincrby(self, name: str, key: str, amount: int = 1) -> "FakePipeline":
        self._queued.append(("hincrby", (name, key, amount), {}))
        return self

    def hset(self, name: str, key: str, value: Any) -> "FakePipeline":
        self._queued.append(("hset", (name, key, value), {}))
        return self

    def expire(self, name: str, seconds: int) -> "FakePipeline":
        self._queued.append(("expire", (name, seconds), {}))
        return self

    def sadd(self, name: str, *values: Any) -> "FakePipeline":
        self._queued.append(("sadd", (name, *values), {}))
        return self

    def set(self, name: str, value: Any, ex: int | None = None) -> "FakePipeline":
        self._queued.append(("set", (name, value), {"ex": ex}))
        return self

    async def execute(self) -> list[Any]:
        results = []
        for command, args, kwargs in self._queued:
            results.append(await getattr(self._client, command)(*args, **kwargs))
        self._queued.clear()
        return results


class BrokenRedis:
    """A server that cannot be reached. Every command raises.

    It is how *Redis is down* is spelled in a test, and it is the input to every
    assertion about the fail-soft posture: an outage must degrade ordering and
    repetition, and must never exclude anybody or empty a surface.
    """

    def __getattr__(self, name: str):
        def _raise(*args: Any, **kwargs: Any):
            raise FakeRedisError(f"redis is unreachable: {name}")

        return _raise

    def pipeline(self, transaction: bool = True) -> "BrokenRedis":
        return self

    def pubsub(self) -> "BrokenRedis":
        """A ``PubSub`` whose every call raises. **The dead subscriber.**

        Returned rather than raised here, because ``Redis.pubsub()`` does not
        touch the socket in real redis-py either — the failure surfaces on
        ``subscribe``, which is where a stream discovers the bus is gone.
        """

        return self

    async def __aenter__(self) -> "BrokenRedis":
        return self

    async def __aexit__(self, *exc_info: Any) -> None:
        return None
