"""*Follow this room until the token that opened it expires.*

**Two calls, because they answer on two different sides of the response line.**
``open`` is the gate: it loads the room, refuses a non-member, and mints the
nudge every stream begins with. ``follow`` is the stream itself. Splitting them
is not a style choice — an async generator's first exception is raised *after*
the framework has already written ``200 text/event-stream``, so a membership
refusal inside the generator would reach a stranger as an empty live stream
instead of as ``conversation_not_found``. The gate has to run before the response
starts, and that is what ``open`` is for.

**Every stream opens with a nudge carrying the room's current ``last_seq``**
(``docs/adr/0147`` §4). It is what makes resume correct without ``Last-Event-ID``
being load-bearing, and it is what repairs a client that missed frames while it
was away: the client fetches from **its own** high-water mark, so one nudge on
connect closes any gap, however old.

**It ends at the access token's expiry** (``docs/adr/0147`` §6). The token
expires four times inside the load balancer's permitted connection life, and a
stream that outlived it would hand a revoked player up to an hour of live
delivery — against the record whose whole point is prompt revocation. The
dividend is that reconnect then runs every fifteen minutes in production rather
than only on deploys, so the hardest-to-test path in this design is the one that
always runs.

**And it ends when the subscriber does** (``docs/adr/0147`` §8). A bus that
cannot be reached closes the stream rather than holding a connection that
delivers nothing, so **a chat that is not live looks not-live** instead of
looking up to date. That is affordable only because of the nudge: the read path
is authoritative and independent, so losing this costs latency, and screen-open
and pull-to-refresh are untouched.

**Nothing is delivered here that the read path could not also answer.** Postgres
stays the only source of truth; this yields two integers and an id.
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import aclosing
from typing import AsyncGenerator, final

from app.kernel import Clock, Instant
from app.modules.conversations.application.a_room_of_yours import ARoomOfYours
from app.modules.conversations.application.commands import FollowConversationCommand
from app.modules.conversations.domain.live import Nudge, NudgeSubscriber

logger = logging.getLogger(__name__)


@final
class FollowConversation:
    """The live half of one room, for somebody who is in it."""

    def __init__(
        self,
        *,
        rooms: ARoomOfYours,
        nudges: NudgeSubscriber,
        clock: Clock,
    ) -> None:
        self._rooms = rooms
        self._nudges = nudges
        self._clock = clock

    async def open(self, command: FollowConversationCommand) -> Nudge:
        """The gate, **and the frame every stream begins with.**

        ``to_read`` and not ``to_append``: this takes no lock and mints no
        sequence — it reads the one the appends have already minted.
        """

        room = (
            await self._rooms.to_read(command.conversation_id, command.reader_id)
        ).conversation
        return Nudge.about(room)

    async def follow(
        self, opening: Nudge, *, until: Instant
    ) -> AsyncGenerator[Nudge, None]:
        """Every nudge for this room, until ``until`` or until the bus is gone.

        **The deadline bounds each wait and never a ``yield``.** A cancel scope
        spanning a suspended ``yield`` would deliver its cancellation into
        whichever task happened to be pulling from this generator, which is not
        this one; bounding only the wait for the next frame keeps the timeout
        where the waiting is.

        **The subscription is opened lazily and closed by ``aclosing``**, so the
        unsubscribe runs whether this ended at the deadline, at a dead bus, or
        because the phone went away mid-frame — the last of which is the common
        case and the one a stray ``return`` would leak.
        """

        yield opening

        async with aclosing(self._nudges.follow(opening.conversation_id)) as nudges:
            while True:
                remaining = (until - self._clock.now()).total_seconds()
                if remaining <= 0:
                    return
                try:
                    async with asyncio.timeout(remaining):
                        nudge = await anext(nudges)
                except (TimeoutError, StopAsyncIteration):
                    # The token's life ran out, or the bus closed the
                    # subscription cleanly. Neither is a fault; the client
                    # reconnects with a fresh token through the same path a
                    # deploy or a backgrounded app takes.
                    return
                except Exception:
                    # **The one place this design closes a stream on purpose.**
                    # A subscriber that is gone must not leave a connection open
                    # delivering nothing, because that is the failure that looks
                    # like a quiet room.
                    logger.warning(
                        "the live channel's subscriber is gone, closing the stream",
                        extra={"conversation_id": str(opening.conversation_id)},
                        exc_info=True,
                    )
                    return
                yield nudge
