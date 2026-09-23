"""Presence in the ephemeral store: **a key per typist, and an index to find them.**

``docs/adr/0156`` §3. Two keys per room and neither of them is in Postgres, which
is the one thing this store may never become: presence is true for five seconds
and a durable row for it would be the single fact in this context that outlives
the room it is about.

**The heartbeat is the key, and Redis owns its expiry.** One
``typing:{conversation}:{player}`` with ``TYPING_TTL`` on it, rewritten on every
heartbeat. Nothing deletes it and nothing may: *stopped typing* is not a message
this design has, so the only thing that can clear an indicator is the key running
out — and a store that expires it is one that cannot forget to.

**The index exists because a read may not scan.** *Who is typing in this room*
has to be answerable without knowing who is **in** the room — membership is
derived from whichever record is arranging (``docs/adr/0146`` §7) and the stream
has closed its database session by the time it asks (``presentation/dependencies``)
— and the alternative to an index is ``SCAN`` over the whole key space, once a
second, per open conversation screen. So a set beside the keys names who has
typed here lately, and it carries the same TTL so that nothing outlives the room.

**The index is a hint and never the answer.** A member is reported only if their
own key is still alive, so a name the set has not dropped costs one slot in an
``MGET`` and can never produce a false indicator. That is what lets the read be a
**pure read**: it deletes nothing, rewrites nothing, and two streams asking at
once cannot race each other into repairing the same set.

**Two round trips, and the second is one command.** The set is small by
construction — a room is two to four people — so the membership read and the
liveness read are one ``SMEMBERS`` and one ``MGET``, never a call per player.

**On the command client, never the subscriber's.** Both of these are ordinary
request/response commands and belong on the pool bounded at both ends; it is the
subscription that cannot live there (``docs/adr/0147`` §5).

**The posture is applied one layer out.** Nothing here catches anything — the
fail-soft wrappers are ``fail_soft_typing.py`` and the composition root never
hands out an unwrapped one, exactly as it does for the nudge publisher and the
matcher's ledgers.
"""

from __future__ import annotations

import math
from uuid import UUID

from redis.asyncio import Redis

from app.modules.conversations.domain.live import TYPING_TTL

#: Where a room's presence lives. **The room is the key** — for the reason the
#: bus's channel is the room's: whoever writes already holds the id, and a
#: per-member shape would make the writer resolve membership first.
KEY_PREFIX = "typing:"

#: The TTL both keys carry, as the whole seconds Redis takes. Rounded **up**, so
#: the stored fact is never shorter than the number the domain published — a
#: heartbeat that expired early would be the flicker ``TYPING_TTL`` is chosen to
#: prevent, arriving through a rounding rule instead.
TTL_SECONDS = int(math.ceil(TYPING_TTL.total_seconds()))


def index_key(conversation_id: UUID) -> str:
    """The set naming who has typed in this room lately."""

    return f"{KEY_PREFIX}{conversation_id}"


def heartbeat_key(conversation_id: UUID, player_id: UUID) -> str:
    """One player's heartbeat in one room. **What actually expires.**"""

    return f"{KEY_PREFIX}{conversation_id}:{player_id}"


class RedisTypingHeartbeat:
    """``TypingHeartbeat`` over ``SET``+``SADD``, in one pipeline.

    Three commands and one round trip. The ``EXPIRE`` on the index is
    unconditional rather than set-on-create: it means the index dies
    ``TYPING_TTL`` after the **last** heartbeat in the room rather than after the
    first, which is what keeps a busy room's index from being reaped under it.
    """

    def __init__(self, client: Redis) -> None:
        self._client = client

    async def typed(self, *, conversation_id: UUID, player_id: UUID) -> None:
        index = index_key(conversation_id)
        async with self._client.pipeline(transaction=False) as pipe:
            pipe.set(heartbeat_key(conversation_id, player_id), "1", ex=TTL_SECONDS)
            pipe.sadd(index, str(player_id))
            pipe.expire(index, TTL_SECONDS)
            await pipe.execute()


class RedisTypingRoster:
    """``TypingRoster`` over ``SMEMBERS`` then ``MGET``. **It writes nothing.**

    A name in the index whose key has gone is simply absent from the answer. An
    id the set holds that will not parse as one is absent too — the same posture
    ``_nudge_in`` takes about a frame it cannot read, and for the same reason:
    somebody else's key in our key space is not a reason to tell a room it is not
    live.
    """

    def __init__(self, client: Redis) -> None:
        self._client = client

    async def who_is_typing(self, conversation_id: UUID) -> frozenset[UUID]:
        # Sorted so the second command asks in a stable order — a set iterated by
        # whatever the store returned is ``docs/adr/0105``'s problem, and here it
        # would be one nobody could see.
        recent = sorted(await self._client.smembers(index_key(conversation_id)))
        # An id that will not parse is somebody else's key in our key space, and
        # is dropped for ``_nudge_in``'s reason: it is not a fact about this room.
        typists = [
            player_id
            for player_id in (_a_player(member) for member in recent)
            if player_id is not None
        ]
        if not typists:
            return frozenset()
        alive = await self._client.mget(
            [heartbeat_key(conversation_id, player_id) for player_id in typists]
        )
        return frozenset(
            player_id
            # `strict`: the store answered about exactly the keys it was asked
            # about, and a length that disagreed would be a fault rather than a
            # shorter roster.
            for player_id, held in zip(typists, alive, strict=True)
            if held is not None
        )


def _a_player(member: str) -> UUID | None:
    try:
        return UUID(member)
    except ValueError:
        return None
