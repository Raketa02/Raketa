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

**Presence is written, expires, and is read back off the store** — the key
shapes, the TTL and the one thing that clears an indicator (`docs/adr/0156`).
Expiry is driven by moving the fake's clock, because *the app was killed* has no
signal to send and there is nothing else to drive.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import get_type_hints
from uuid import UUID, uuid4

import pytest
from fastapi import params

from app.bootstrap.composition import (
    build_nudge_publisher,
    build_nudge_subscriber,
    build_typing_heartbeat,
    build_typing_roster,
)
from app.kernel import Instant, InvariantViolated, instant
from app.modules.conversations.application.follow_conversation import (
    FollowConversation,
)
from app.modules.conversations.domain.live import (
    LIVE_CHANNEL_VERSION,
    TYPING_CADENCE,
    TYPING_CHECK,
    TYPING_TTL,
    Nudge,
    Typing,
)
from app.infrastructure.redis_client import get_redis, get_redis_subscriber
from app.modules.conversations.infrastructure.redis_live_channel import channel_for
from app.modules.conversations.presentation.dependencies import (
    get_nudge_publisher,
    get_nudge_subscriber,
    get_typing_heartbeat,
    get_typing_roster,
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


A_READER = UUID("99999999-9999-9999-9999-999999999999")


class NobodyIsTyping:
    """A ``TypingRoster`` for the tests that are about nudges."""

    async def who_is_typing(self, conversation_id):
        return frozenset()


class TheWallClock:
    """A clock that actually moves.

    **The presence tests need one and the nudge tests must not have one.** A
    frozen clock makes *when does this token expire* answerable without waiting,
    which is what every test above wants; but the roster check is a second,
    shorter deadline inside the same loop, so a stream whose clock never moves
    reaches the check for ever and reaches the token's expiry never.
    """

    def now(self) -> Instant:
        return _now()


def _following(store, *, now, typists=None, clock=None) -> FollowConversation:
    return FollowConversation(
        rooms=_ARoomOfMine(None),
        nudges=build_nudge_subscriber(store),
        typists=typists or NobodyIsTyping(),
        clock=clock or FrozenClock(now),
    )


async def _drain(use_case: FollowConversation, opening: Nudge, until: Instant):
    return [
        frame
        async for frame in use_case.follow(opening, reader_id=A_READER, until=until)
    ]


async def test_the_stream_ends_at_the_deadline_and_unsubscribes():
    store = FakeRedis()
    now = _now()
    use_case = _following(store, now=now)
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
    use_case = _following(store, now=now)
    opening = Nudge(conversation_id=A_ROOM, last_seq=0)

    frames = await _drain(use_case, opening, instant(now - timedelta(seconds=1)))

    assert frames == [opening]


async def test_a_dead_subscriber_closes_the_stream_after_the_opening_frame():
    """A chat that is not live has to **look** not-live (`docs/adr/0147` §8)."""

    now = _now()
    use_case = _following(BrokenRedis(), now=now)
    opening = Nudge(conversation_id=A_ROOM, last_seq=2)

    frames = await asyncio.wait_for(
        _drain(use_case, opening, instant(now + timedelta(hours=1))), timeout=5
    )

    assert frames == [opening]


async def test_every_nudge_published_while_following_is_delivered():
    store = FakeRedis()
    now = _now()
    use_case = _following(store, now=now)
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
# Presence: the keys, the expiry, and the one thing that clears an indicator
# ---------------------------------------------------------------------------


A_TYPIST = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
ANOTHER_TYPIST = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")


async def test_a_heartbeat_is_one_key_per_typist_and_one_index_per_room():
    """The shapes, asserted off the store rather than off the adapter.

    The index is what makes *who is typing here* answerable without knowing who
    is **in** the room, which the stream cannot know: membership is derived and
    the request's database session is closed before the first frame.
    """

    store = FakeRedis()

    await build_typing_heartbeat(store).typed(
        conversation_id=A_ROOM, player_id=A_TYPIST
    )

    assert store.keys_held() == {
        f"typing:{A_ROOM}",
        f"typing:{A_ROOM}:{A_TYPIST}",
    }


async def test_both_keys_carry_the_ttl_the_domain_published():
    """`TYPING_TTL` and not a number the adapter chose."""

    store = FakeRedis()

    await build_typing_heartbeat(store).typed(
        conversation_id=A_ROOM, player_id=A_TYPIST
    )

    assert store.ttl_of(f"typing:{A_ROOM}") == TYPING_TTL.total_seconds()
    assert store.ttl_of(f"typing:{A_ROOM}:{A_TYPIST}") == TYPING_TTL.total_seconds()


async def test_the_roster_is_whoever_has_not_expired():
    """**The whole mechanism**, and there is no other one (`docs/adr/0156`).

    Nobody says *stopped*. One typist keeps typing and one is killed mid-word,
    and the answer changes because a key ran out — which is the only thing in
    this design that can change it.
    """

    store = FakeRedis()
    heartbeat, roster = build_typing_heartbeat(store), build_typing_roster(store)
    await heartbeat.typed(conversation_id=A_ROOM, player_id=A_TYPIST)
    await heartbeat.typed(conversation_id=A_ROOM, player_id=ANOTHER_TYPIST)

    assert await roster.who_is_typing(A_ROOM) == {A_TYPIST, ANOTHER_TYPIST}

    # Three seconds on: one of them is still typing and the other's phone is
    # face down on a table.
    store.advance(TYPING_CADENCE.total_seconds())
    await heartbeat.typed(conversation_id=A_ROOM, player_id=A_TYPIST)
    store.advance(TYPING_TTL.total_seconds() - TYPING_CADENCE.total_seconds() + 0.1)

    assert await roster.who_is_typing(A_ROOM) == {A_TYPIST}


async def test_the_index_is_a_hint_and_never_the_answer():
    """A name the set has not dropped costs one slot in an `MGET`, and nothing
    else — which is what lets the read be a **pure read** that repairs nothing
    and races nobody."""

    store = FakeRedis()
    heartbeat, roster = build_typing_heartbeat(store), build_typing_roster(store)
    await heartbeat.typed(conversation_id=A_ROOM, player_id=A_TYPIST)
    # The room stays busy, so the index is kept alive past the heartbeat inside
    # it — the exact state a stale name lives in.
    store.advance(TYPING_TTL.total_seconds() - 0.1)
    await heartbeat.typed(conversation_id=A_ROOM, player_id=ANOTHER_TYPIST)
    store.advance(0.2)

    assert f"{A_TYPIST}" in await store.smembers(f"typing:{A_ROOM}")
    assert await roster.who_is_typing(A_ROOM) == {ANOTHER_TYPIST}


async def test_a_room_where_nobody_has_typed_answers_nobody():
    """And it answers it in one command, not a scan of the key space."""

    assert await build_typing_roster(FakeRedis()).who_is_typing(A_ROOM) == frozenset()


async def test_a_heartbeat_onto_a_store_that_is_gone_costs_one_second_of_a_courtesy():
    """Fail soft, like the publisher and for a stronger version of its reason."""

    await build_typing_heartbeat(BrokenRedis()).typed(
        conversation_id=A_ROOM, player_id=A_TYPIST
    )


async def test_a_roster_read_onto_a_store_that_is_gone_reports_nobody_typing():
    """**The departure from the subscriber beside it** (`docs/adr/0156` §6).

    A subscription *is* the room's liveness and closes the stream; a roster is a
    courtesy read on the client with a two-second deadline, asked once a second
    by every open conversation screen. Failing it loud would let a merely slow
    store close every healthy stream on the platform.
    """

    assert await build_typing_roster(BrokenRedis()).who_is_typing(A_ROOM) == frozenset()


async def test_a_polling_stream_complains_once_per_outage_and_not_once_per_read(
    caplog,
):
    """**The one departure from the fail-soft wrappers beside it.**

    Everything else that degrades in this repository is asked at human pace, and
    one warning per failure is right there. A roster is asked once a second for
    the life of a stream, so a line per read would turn one outage into a log
    entry per second per screen — which is how a real signal gets buried. The
    wrapper is built per stream, so *first failure, then quiet until it works
    again* is one line per stream per outage.
    """

    roster = build_typing_roster(BrokenRedis())

    with caplog.at_level(logging.WARNING):
        for _ in range(5):
            assert await roster.who_is_typing(A_ROOM) == frozenset()

    assert len(caplog.records) == 1


async def test_a_store_that_comes_back_re_arms_the_complaint():
    """A second outage is a second thing to know about, not a repeat of the first."""

    class _Flaky:
        def __init__(self) -> None:
            self.reachable = False

        async def who_is_typing(self, conversation_id):
            if not self.reachable:
                raise FakeRedisError("redis is unreachable")
            return frozenset()

    from app.modules.conversations.infrastructure.fail_soft_typing import (
        FailSoftTypingRoster,
    )

    store = _Flaky()
    roster = FailSoftTypingRoster(store)

    assert roster._degraded is False
    await roster.who_is_typing(A_ROOM)
    assert roster._degraded is True
    store.reachable = True
    await roster.who_is_typing(A_ROOM)
    assert roster._degraded is False


async def test_a_stream_reports_whoever_the_roster_names_and_never_the_reader():
    """The filter is the stream's, because only the stream knows whose it is."""

    store = FakeRedis()
    now = _now()
    await build_typing_heartbeat(store).typed(
        conversation_id=A_ROOM, player_id=A_TYPIST
    )
    await build_typing_heartbeat(store).typed(
        conversation_id=A_ROOM, player_id=A_READER
    )
    use_case = _following(
        store,
        now=now,
        typists=build_typing_roster(store),
        clock=TheWallClock(),
    )
    opening = Nudge(conversation_id=A_ROOM, last_seq=1)

    frames = await asyncio.wait_for(
        _drain(
            use_case,
            opening,
            instant(_now() + TYPING_CHECK + timedelta(milliseconds=300)),
        ),
        timeout=10,
    )

    assert frames == [opening, Typing.of(A_ROOM, [A_TYPIST])]


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
    # **Presence is on the command client, both ways** — the roster is read from
    # inside a stream, which is the one place it would be tempting to reach for
    # the deadline-free pool, and a courtesy read wants the deadline every other
    # command has (`docs/adr/0156` §6).
    assert _client_behind(get_typing_heartbeat) is get_redis
    assert _client_behind(get_typing_roster) is get_redis


def _client_behind(declaration):
    """What ``Depends`` the declaration's ``store`` parameter is annotated with."""

    annotation = get_type_hints(declaration, include_extras=True)["store"]
    (depends,) = (
        piece for piece in annotation.__metadata__ if isinstance(piece, params.Depends)
    )
    return depends.dependency
