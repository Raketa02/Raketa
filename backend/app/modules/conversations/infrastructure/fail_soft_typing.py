"""Where *presence is a courtesy* stops being prose and starts being enforced.

Nothing here is evidence for anything and nothing here survives five seconds, so
a store that cannot be reached costs a room its typing indicator and costs
nobody anything else. That is a collapse — *we could not tell* reading as
*there is nothing to tell* — and it is safe here for the strongest version of
that reason: an empty roster is **also** what a room where nobody is typing
answers, which is what a room is almost all of the time.

**Both directions are soft, and that is the departure worth stating**
(``docs/adr/0156`` §6). The nudge ports fail in opposite directions: a publish is
a courtesy and a subscription *is* the room's liveness, so the second closes the
stream. A roster read is neither — it is a courtesy on the **command** client,
the one with a two-second deadline, asked once a second by every open
conversation screen. Failing it loud would let a merely slow store close every
healthy stream on the platform, which is a worse answer than the one the outage
deserves.

**And it complains on the transition rather than on every read.** Everything else
in this repository that fails soft is asked at human pace — a send, a search —
and one warning per failure is exactly right there. This one is asked once a
second for the life of a stream, so a per-read line would turn one outage into a
log entry per second per screen, which is how a real signal gets buried. Each
wrapper is built per stream by the composition root, so *first failure, then
quiet until it works again* is one line per stream per outage: enough to see it,
never enough to drown in.
"""

from __future__ import annotations

import logging
from uuid import UUID

from app.modules.conversations.domain.live import TypingHeartbeat, TypingRoster

logger = logging.getLogger(__name__)


class FailSoftTypingHeartbeat:
    """A ``TypingHeartbeat`` whose outage costs one second of an indicator."""

    def __init__(self, inner: TypingHeartbeat) -> None:
        self._inner = inner

    async def typed(self, *, conversation_id: UUID, player_id: UUID) -> None:
        try:
            await self._inner.typed(
                conversation_id=conversation_id, player_id=player_id
            )
        except Exception:
            # Warning rather than error, on ``fail_soft_nudges``' argument: a
            # store restarting is an expected state and nothing is broken for
            # the player, who keeps typing and keeps sending.
            logger.warning(
                "the ephemeral store is unavailable, nobody will be shown typing",
                extra={
                    "conversation_id": str(conversation_id),
                    "player_id": str(player_id),
                },
                exc_info=True,
            )


class FailSoftTypingRoster:
    """A ``TypingRoster`` that answers *nobody* when it cannot answer at all."""

    def __init__(self, inner: TypingRoster) -> None:
        self._inner = inner
        #: Whether the last read failed. **Per instance, and the instance is per
        #: stream** — see the module docstring for why this is not a per-read
        #: log line.
        self._degraded = False

    async def who_is_typing(self, conversation_id: UUID) -> frozenset[UUID]:
        try:
            answer = await self._inner.who_is_typing(conversation_id)
        except Exception:
            if not self._degraded:
                self._degraded = True
                logger.warning(
                    "the ephemeral store is unavailable, "
                    "this stream reports nobody typing",
                    extra={"conversation_id": str(conversation_id)},
                    exc_info=True,
                )
            return frozenset()
        self._degraded = False
        return answer
