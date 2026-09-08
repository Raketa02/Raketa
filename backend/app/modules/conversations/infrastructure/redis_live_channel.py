"""The live channel over Redis pub/sub, **keyed on the conversation.**

``docs/adr/0147`` §5. One channel per room, ``conversation:{id}``, subscribed and
unsubscribed as streams open and close.

**Per conversation and not per user**, which is the research's shape refused by
name: a per-user channel forces the publisher to resolve *who is in this room*
before it can publish, and membership is derived from whichever record is
arranging — a read added to the append path to buy nothing. Per-conversation, the
publisher already holds the id. It just appended to it.

**The bus payload is the same nudge that reaches the phone**, so at-most-once
delivery is adequate and Redis Streams are not needed here. A subscriber that
misses a notification loses **latency, not data**: the read path is
authoritative, and the next nudge repairs the gap because the client fetches from
its own high-water mark.

**Two clients, and they are different clients on purpose.** A publish is a
command and goes on the process's ordinary pool, bounded at both ends. A
subscription is a blocking read with no deadline and gets the client
``create_redis_subscriber_client`` hands out — ``docs/adr/0147`` §5 and #342: a
``socket_timeout`` on a subscription does not merely reconnect, it raises at the
caller every two seconds, and whatever was published in the gap is gone because
pub/sub replays nothing to a channel nobody was on.

**There is no supervised reconnect loop here, and its absence is the design
rather than an omission.** ``docs/adr/0147`` §8 asks for one because it pictures
a **process-wide** subscriber: one long-lived task fanning out to every open
stream, whose quiet death would leave every connection on it delivering nothing.
This is per **stream** instead — one ``PubSub`` opened when a conversation screen
opens and dropped when it closes — so there is no shared task to supervise, and
the failure §8 wants repaired is repaired by the thing §6 already guarantees: a
subscription that dies takes **its own** stream down with it, and that client
reconnects, as it does every fifteen minutes anyway. The other two parts of §8
stand exactly as written — ``/health`` says nothing about Redis, and a server
whose subscriber is gone closes the stream. **What is genuinely given up** is
recovery *within* one token's life: a bus that blips at minute two leaves that
screen unlive until minute fifteen rather than for a second. That is the price of
having nothing to supervise, and it is the same price a deploy already charges.

**Liveness on the subscription is left where the amendment left it.** Dropping
the read deadline drops the crude thing that noticed a connection which had died
without saying so, and this adapter deliberately adds none of the three
replacements: the stream is bounded by the access token's expiry
(``application/follow_conversation.py``), so the longest a silently-dead socket
can go unnoticed is one token's life, and the reconnect that follows is the same
code path a deploy or a backgrounded app takes. A keepalive here would be a
second liveness mechanism with a different period, chosen against no measurement.

**The posture is applied one layer out.** Nothing here catches anything: the
fail-soft publisher is ``fail_soft_nudges.py`` and the composition root never
hands out an unwrapped one, exactly as it does for the matcher's ledgers.
"""

from __future__ import annotations

import json
import logging
from typing import Any, AsyncGenerator
from uuid import UUID

from redis.asyncio import Redis

from app.modules.conversations.domain.live import LIVE_CHANNEL_VERSION, Nudge

logger = logging.getLogger(__name__)

#: The channel every room's nudges ride. **The id is the key** — see the module
#: docstring for why it is not the member's.
CHANNEL_PREFIX = "conversation:"


def channel_for(conversation_id: UUID) -> str:
    """The one channel this room publishes on and its followers subscribe to."""

    return f"{CHANNEL_PREFIX}{conversation_id}"


#: The wire names, spelled once. They are the **same three** the route declares
#: (``presentation/schemas.py``), because a bus payload that drifted from the
#: envelope would be a translation nobody wrote down.
_V = "v"
_CONVERSATION_ID = "conversation_id"
_LAST_SEQ = "last_seq"


class RedisNudgePublisher:
    """``NudgePublisher`` over ``PUBLISH``, on the process's ordinary client.

    A publish is a request/response command like any other, so it belongs on the
    pool every command path draws from and inherits that pool's two deadlines. It
    is the *subscription* that cannot live there.
    """

    def __init__(self, client: Redis) -> None:
        self._client = client

    async def nudge(self, nudge: Nudge) -> None:
        await self._client.publish(
            channel_for(nudge.conversation_id),
            json.dumps(
                {
                    _V: nudge.v,
                    _CONVERSATION_ID: str(nudge.conversation_id),
                    _LAST_SEQ: nudge.last_seq,
                }
            ),
        )


class RedisNudgeSubscriber:
    """``NudgeSubscriber`` over one ``PubSub``, on the subscriber's own client.

    **One ``PubSub`` per open stream**, opened when the stream opens and closed
    when it ends — including when it ends because the phone went away, since the
    generator's ``finally`` runs whether the iteration finished or was closed.
    """

    def __init__(self, client: Redis) -> None:
        self._client = client

    async def follow(self, conversation_id: UUID) -> AsyncGenerator[Nudge, None]:
        channel = channel_for(conversation_id)
        pubsub = self._client.pubsub()
        try:
            await pubsub.subscribe(channel)
            async for message in pubsub.listen():
                nudge = _nudge_in(message, conversation_id)
                if nudge is not None:
                    yield nudge
        finally:
            # `type: ignore` for the reason `redis_client.close_redis` carries
            # one: the obsolete `types-redis` stubs in the dev group shadow
            # redis-py's own inline types and predate `aclose`, which exists and
            # is the spelling `close` was deprecated in favour of.
            await pubsub.aclose()  # type: ignore[attr-defined]


def _nudge_in(message: Any, conversation_id: UUID) -> Nudge | None:
    """One frame off the bus, or ``None`` for anything that is not one.

    ``listen()`` yields subscribe confirmations as well as messages, so the type
    check is not defensive — it is most of what comes back on a quiet channel.

    **A frame that will not parse is dropped rather than raised.** Raising would
    close the stream, and closing a live chat because somebody published rubbish
    on our channel is a worse answer than the one dropping gives: the room is
    still live, the next nudge still repairs whatever this one would have said,
    and the log line is what stops the loss being silent.
    """

    if message.get("type") != "message":
        return None
    try:
        frame = json.loads(message["data"])
        return Nudge(
            conversation_id=conversation_id,
            last_seq=int(frame[_LAST_SEQ]),
            v=int(frame.get(_V, LIVE_CHANNEL_VERSION)),
        )
    except Exception:
        logger.warning(
            "unreadable frame on a conversation channel, dropping",
            extra={"conversation_id": str(conversation_id)},
            exc_info=True,
        )
        return None
