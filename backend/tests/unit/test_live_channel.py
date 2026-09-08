"""The live channel below HTTP: the frame, the bus, and what closes a stream.

Everything here runs against `tests/unit/fake_redis.py` — the stand-in for the
*server*, so that `RedisNudgePublisher` and `RedisNudgeSubscriber` (the classes
that decide the channel key and the frame's encoding) are exercised rather than
stubbed past. **No test in this suite needs Redis running.**

What is asserted here and nowhere else:

**The frame is exactly three fields**, on the bus as well as on the wire.

**The channel is the conversation's**, never the member's.

**A publish fails soft and a subscription does not**, which is the asymmetry the
whole degradation story rests on.

**The stream ends at the deadline and at a dead bus**, and unsubscribes either
way.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta, timezone
from typing import get_type_hints
from uuid import UUID, uuid4

import pytest
from fastapi import params

from app.bootstrap.composition import build_nudge_publisher, build_nudge_subscriber
from app.kernel import Instant, InvariantViolated, instant
from app.modules.conversations.application.follow_conversation import (
    FollowConversation,
)
from app.modules.conversations.domain.live import LIVE_CHANNEL_VERSION, Nudge
from app.infrastructure.redis_client import get_redis, get_redis_subscriber
from app.modules.conversations.infrastructure.redis_live_channel import channel_for
from app.modules.conversations.presentation.dependencies import (
    get_nudge_publisher,
    get_nudge_subscriber,
)
from tests.unit.fake_redis import BrokenRedis, FakeRedis, FakeRedisError

A_ROOM = UUID("11111111-1111-1111-1111-111111111111")


class FrozenClock:
    def __init__(self, at: Instant) -> None:
        self._at = at

    def now(self) -> Instant:
        return self._at


def _now() -> Instant:
    return instant(datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# The frame
# ---------------------------------------------------------------------------


async def test_the_frame_on_the_bus_is_exactly_the_three_fields():
    store = FakeRedis()
    await build_nudge_publisher(store).nudge(Nudge(conversation_id=A_ROOM, last_seq=7))

    channel, payload = store.published[-1]
    assert channel == f"conversation:{A_ROOM}"
    assert json.loads(payload) == {
        "v": LIVE_CHANNEL_VERSION,
        "conversation_id": str(A_ROOM),
        "last_seq": 7,
    }


async def test_the_channel_is_the_conversations_and_never_a_members():
    """Per-user would force a membership read into the append path to buy nothing."""

    store = FakeRedis()
    a_member = uuid4()
    await build_nudge_publisher(store).nudge(Nudge(conversation_id=A_ROOM, last_seq=1))

    assert store.published[-1][0] == channel_for(A_ROOM)
    assert str(a_member) not in store.published[-1][0]


async def test_a_room_cannot_have_landed_a_negative_count():
    with pytest.raises(InvariantViolated):
        Nudge(conversation_id=A_ROOM, last_seq=-1)


# ---------------------------------------------------------------------------
# The two postures
# ---------------------------------------------------------------------------


async def test_a_publish_onto_a_store_that_is_gone_costs_the_room_its_liveness_only():
    """The entry is already committed. An outage may not undo that."""

    await build_nudge_publisher(BrokenRedis()).nudge(
        Nudge(conversation_id=A_ROOM, last_seq=3)
    )


async def test_a_subscription_onto_a_store_that_is_gone_raises():
    """The opposite posture, deliberately: a dead bus has to close the stream."""

    following = build_nudge_subscriber(BrokenRedis()).follow(A_ROOM)
    with pytest.raises(FakeRedisError):
        await anext(following)


async def test_a_frame_that_will_not_parse_is_dropped_and_the_stream_lives():
    store = FakeRedis()
    following = build_nudge_subscriber(store).follow(A_ROOM)

    async def _next() -> Nudge:
        return await anext(following)

    reader = asyncio.create_task(_next())
    await asyncio.sleep(0)
    await store.publish(channel_for(A_ROOM), "{ not a frame")
    await store.publish(
        channel_for(A_ROOM),
        json.dumps({"v": 1, "conversation_id": str(A_ROOM), "last_seq": 9}),
    )

    assert (await asyncio.wait_for(reader, timeout=1)) == Nudge(
        conversation_id=A_ROOM, last_seq=9
    )
    await following.aclose()


# ---------------------------------------------------------------------------
# What a nudge reaches, and what it does not
# ---------------------------------------------------------------------------


async def test_a_frame_published_while_nobody_follows_reaches_nobody():
    """At-most-once, and it is the property the whole design is built on.

    Redis pub/sub retains nothing, so a nudge published to an empty channel is
    simply gone. That costs latency and never data: the client fetches from its
    own high-water mark, so the next nudge — or the one every stream opens with —
    delivers everything the lost one would have announced.
    """

    store = FakeRedis()
    assert store.subscribers_on(channel_for(A_ROOM)) == 0
    delivered = await store.publish(channel_for(A_ROOM), "anything")
    assert delivered == 0


async def test_the_subscription_is_dropped_when_the_iteration_ends():
    store = FakeRedis()
    following = build_nudge_subscriber(store).follow(A_ROOM)

    reader = asyncio.create_task(anext(following))
    await asyncio.sleep(0)
    assert store.subscribers_on(channel_for(A_ROOM)) == 1

    reader.cancel()
    await asyncio.gather(reader, return_exceptions=True)
    await following.aclose()
    assert store.subscribers_on(channel_for(A_ROOM)) == 0


# ---------------------------------------------------------------------------
# The two ways a stream ends
# ---------------------------------------------------------------------------


class _ARoomOfMine:
    """The gate, already answered. ``FollowConversation.open`` is tested over HTTP."""

    def __init__(self, room) -> None:
        self._room = room

    async def to_read(self, conversation_id, reader_id):
        return self._room


async def _drain(use_case: FollowConversation, opening: Nudge, until: Instant):
    return [nudge async for nudge in use_case.follow(opening, until=until)]


async def test_the_stream_ends_at_the_deadline_and_unsubscribes():
    store = FakeRedis()
    now = _now()
    use_case = FollowConversation(
        rooms=_ARoomOfMine(None),
        nudges=build_nudge_subscriber(store),
        clock=FrozenClock(now),
    )
    opening = Nudge(conversation_id=A_ROOM, last_seq=4)

    frames = await asyncio.wait_for(
        _drain(use_case, opening, instant(now + timedelta(milliseconds=50))),
        timeout=5,
    )

    assert frames == [opening]
    assert store.subscribers_on(channel_for(A_ROOM)) == 0


async def test_a_deadline_already_past_yields_the_opening_frame_and_stops():
    """A token with seconds left is still a token, and one with none closes at once."""

    store = FakeRedis()
    now = _now()
    use_case = FollowConversation(
        rooms=_ARoomOfMine(None),
        nudges=build_nudge_subscriber(store),
        clock=FrozenClock(now),
    )
    opening = Nudge(conversation_id=A_ROOM, last_seq=0)

    frames = await _drain(use_case, opening, instant(now - timedelta(seconds=1)))

    assert frames == [opening]


async def test_a_dead_subscriber_closes_the_stream_after_the_opening_frame():
    """A chat that is not live has to **look** not-live (`docs/adr/0147` §8)."""

    now = _now()
    use_case = FollowConversation(
        rooms=_ARoomOfMine(None),
        nudges=build_nudge_subscriber(BrokenRedis()),
        clock=FrozenClock(now),
    )
    opening = Nudge(conversation_id=A_ROOM, last_seq=2)

    frames = await asyncio.wait_for(
        _drain(use_case, opening, instant(now + timedelta(hours=1))), timeout=5
    )

    assert frames == [opening]


async def test_every_nudge_published_while_following_is_delivered():
    store = FakeRedis()
    now = _now()
    use_case = FollowConversation(
        rooms=_ARoomOfMine(None),
        nudges=build_nudge_subscriber(store),
        clock=FrozenClock(now),
    )
    opening = Nudge(conversation_id=A_ROOM, last_seq=1)
    publisher = build_nudge_publisher(store)

    async def _say_two_things() -> None:
        while store.subscribers_on(channel_for(A_ROOM)) == 0:
            await asyncio.sleep(0)
        await publisher.nudge(Nudge(conversation_id=A_ROOM, last_seq=2))
        await publisher.nudge(Nudge(conversation_id=A_ROOM, last_seq=3))

    frames, _ = await asyncio.wait_for(
        asyncio.gather(
            _drain(use_case, opening, instant(now + timedelta(milliseconds=300))),
            _say_two_things(),
        ),
        timeout=5,
    )

    assert [frame.last_seq for frame in frames] == [1, 2, 3]
    assert all(frame.v == LIVE_CHANNEL_VERSION for frame in frames)


# ---------------------------------------------------------------------------
# The wiring
# ---------------------------------------------------------------------------


def test_the_subscription_is_declared_over_the_subscribers_own_client():
    """*Which pool is this on* is invisible at rest, so it is asserted here.

    Both clients hold the same address and differ only in a read deadline, so a
    subscription accidentally declared over the command pool looks identical in
    every test that uses one fake for both — and in production it raises every
    two seconds and loses whatever was published while it reconnected (#342).
    This walks the declarations instead.
    """

    assert _client_behind(get_nudge_subscriber) is get_redis_subscriber
    assert _client_behind(get_nudge_publisher) is get_redis


def _client_behind(declaration):
    """What ``Depends`` the declaration's ``store`` parameter is annotated with."""

    annotation = get_type_hints(declaration, include_extras=True)["store"]
    (depends,) = (
        piece for piece in annotation.__metadata__ if isinstance(piece, params.Depends)
    )
    return depends.dependency
