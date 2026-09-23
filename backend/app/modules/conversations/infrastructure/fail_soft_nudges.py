"""Where *a publish is a courtesy* stops being prose and starts being enforced.

The entry is already durable in Postgres by the time anything here runs. What a
nudge buys is that somebody's phone finds out **now** rather than when they next
open the screen — and a bus that is down may cost a room its liveness, but it may
never cost anybody their message.

**One wrapper at one seam**, for the reason ``fail_soft_ledgers.py`` gives at
length: a ``try`` inside the adapter makes *the bus said nothing* and *the bus
could not be reached* indistinguishable from outside, and a ``try`` at each call
site makes the posture a discipline. The composition root never hands out an
unwrapped publisher, so there is no call site that could forget.

**It catches broadly, deliberately.** A store that raises and a store that
answers something impossible are the same event to a courtesy, and the log line
is what keeps the degradation from being silent — a chat that quietly stopped
being live is exactly the failure that hides.

**Nothing here wraps the subscriber, and that asymmetry is the design.** A
subscription *is* the liveness, so it fails loud and closes the stream
(``docs/adr/0147`` §8): a chat that is not live has to look not-live, and a
connection held open delivering nothing looks up to date.
"""

from __future__ import annotations

import logging

from app.modules.conversations.domain.live import Nudge, NudgePublisher

logger = logging.getLogger(__name__)


class FailSoftNudgePublisher:
    """A ``NudgePublisher`` whose outage costs a room its liveness, and nothing else."""

    def __init__(self, inner: NudgePublisher) -> None:
        self._inner = inner

    async def nudge(self, nudge: Nudge) -> None:
        try:
            await self._inner.nudge(nudge)
        except Exception:
            # Warning rather than error, on `fail_soft_ledgers`' argument: a bus
            # restarting is an expected state and nothing is broken for the
            # player, who keeps reading the room. It is not info either — a chat
            # that silently stopped being live must not read like a quiet one.
            logger.warning(
                "the live channel is unavailable, the room is not live",
                extra={
                    "conversation_id": str(nudge.conversation_id),
                    "last_seq": nudge.last_seq,
                },
                exc_info=True,
            )
