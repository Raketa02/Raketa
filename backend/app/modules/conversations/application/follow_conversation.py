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

**Nothing that a nudge announces is delivered here that the read path could not
also answer.** Postgres stays the only source of truth for anything that
happened; a nudge yields two integers and an id.

**And beside the nudges, presence** (``docs/adr/0156``). The second frame is not
announced by anything — a heartbeat is written to an ephemeral store by whoever
is typing, and nothing publishes when one **expires**, because expiry is the
absence of a write. So this asks: every ``TYPING_CHECK`` it reads the room's
roster and yields a frame **when the answer has changed**, including changing to
nobody. Three things about that are load-bearing.

**The clear is the whole reason it is a poll.** There is no *stopped* message
anywhere in this design, deliberately, so the only event that could carry one is
one that never fires. A design that pushed the arrival and timed out the clear
would still need this timer and would need a cached set beside it whose staleness
is a second bug; asking the store is one mechanism where that is two.

**A frame is yielded on change and never on a tick.** A room where nobody is
typing costs a read and produces nothing, so a quiet stream is exactly as quiet
as it was before this existed — which is what keeps ``docs/adr/0147`` §3's *a
lost frame costs nothing* true for the frames that are still nudges. The first
check is due **the moment the stream opens**, because that is when it matters
most: a phone opens this screen because somebody is talking to them.

**The reader is filtered out of their own room's answer**, here rather than at
the store, because the store's answer is the same for everybody following the
room and only this knows whose stream it is. Without it the composer draws an
indicator for the person using it.

**The subscription is awaited as a task rather than under a timeout**, and that
is not a style choice. ``asyncio.timeout`` around ``anext`` **cancels** it, and a
cancelled ``anext`` delivers the cancellation into the subscriber's own frame and
finishes it — which was harmless when the only deadline was the last one this
loop ever waited, and would close every subscription once a second now that there
is a second, shorter clock in here.
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import aclosing
from typing import AsyncGenerator, final
from uuid import UUID

from app.kernel import Clock, Instant, instant
from app.modules.conversations.application.a_room_of_yours import ARoomOfYours
from app.modules.conversations.application.commands import FollowConversationCommand
from app.modules.conversations.domain.live import (
    TYPING_CHECK,
    Nudge,
    NudgeSubscriber,
    Typing,
    TypingRoster,
)

logger = logging.getLogger(__name__)


@final
class FollowConversation:
    """The live half of one room, for somebody who is in it."""

    def __init__(
        self,
        *,
        rooms: ARoomOfYours,
        nudges: NudgeSubscriber,
        typists: TypingRoster,
        clock: Clock,
    ) -> None:
        self._rooms = rooms
        self._nudges = nudges
        self._typists = typists
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
        self, opening: Nudge, *, reader_id: UUID, until: Instant
    ) -> AsyncGenerator[Nudge | Typing, None]:
        """Every frame for this room, until ``until`` or until the bus is gone.

        **Two clocks, and only one of them ends anything.** ``until`` is the
        access token's own expiry and closes the stream; ``TYPING_CHECK`` is how
        often the roster is re-read, and reaching it means only that a read is
        due. Each wait is bounded by whichever comes first, so the deadline is
        never overshot by a poll and a poll is never skipped by the deadline.

        **The deadline bounds a wait and never a ``yield``.** A cancel scope
        spanning a suspended ``yield`` would deliver its cancellation into
        whichever task happened to be pulling from this generator, which is not
        this one; bounding only the waiting keeps the timeout where the waiting
        is.

        **The subscription is opened lazily and closed by ``aclosing``**, so the
        unsubscribe runs whether this ended at the deadline, at a dead bus, or
        because the phone went away mid-frame — the last of which is the common
        case and the one a stray ``return`` would leak. The pending pull is
        cancelled **and awaited** first: ``aclose`` on a generator whose
        ``__anext__`` is still running raises, and this is the one place both
        could be true at once.
        """

        yield opening

        #: Who this reader is currently being shown as typing. Compared rather
        #: than re-sent, so a room where nothing changes stays silent.
        showing: tuple[UUID, ...] = ()
        async with aclosing(self._nudges.follow(opening.conversation_id)) as nudges:
            pulling: asyncio.Task[Nudge] | None = None
            # **Due immediately**, so a stream opened into a room where somebody
            # is already typing says so at once rather than a check later. That
            # is the moment it matters most: a phone opens this screen because
            # somebody is talking to them.
            check_at = self._clock.now()
            try:
                while True:
                    now = self._clock.now()
                    token_in = (until - now).total_seconds()
                    if token_in <= 0:
                        return
                    check_in = max(0.0, (check_at - now).total_seconds())
                    # **Which clock bounded the wait is decided here and read
                    # back below**, rather than re-asked of the clock when the
                    # wait ends: a wait that ran to a deadline *is* that deadline
                    # arriving, and a second reading is a second answer.
                    bounded_by_the_token = token_in <= check_in
                    if pulling is None:
                        pulling = asyncio.ensure_future(anext(nudges))
                    done, _ = await asyncio.wait(
                        {pulling}, timeout=min(token_in, check_in)
                    )
                    if pulling in done:
                        pull, pulling = pulling, None
                        try:
                            nudge = pull.result()
                        except StopAsyncIteration:
                            # The bus closed the subscription cleanly. Not a
                            # fault; the client reconnects with a fresh token
                            # through the same path a deploy takes.
                            return
                        except Exception:
                            # **The one place this design closes a stream on
                            # purpose.** A subscriber that is gone must not leave
                            # a connection open delivering nothing, because that
                            # is the failure that looks like a quiet room.
                            logger.warning(
                                "the live channel's subscriber is gone, "
                                "closing the stream",
                                extra={"conversation_id": str(opening.conversation_id)},
                                exc_info=True,
                            )
                            return
                        yield nudge
                        continue
                    if bounded_by_the_token:
                        # The token's life ran out while we waited. The roster
                        # below is a courtesy and this is a credential.
                        return
                    frame = await self._what_changed(
                        opening.conversation_id, reader_id=reader_id, showing=showing
                    )
                    # **Scheduled from the moment the read came back**, not from
                    # the moment it was asked for. A store answering slowly — or
                    # refusing instantly — would otherwise leave no gap at all
                    # between one read and the next, which is a poll loop with
                    # its interval removed by exactly the fault that most needs
                    # one.
                    check_at = instant(self._clock.now() + TYPING_CHECK)
                    if frame is not None:
                        showing = frame.player_ids
                        yield frame
            finally:
                if pulling is not None:
                    pulling.cancel()
                    try:
                        await pulling
                    except asyncio.CancelledError:
                        pass
                    except Exception:
                        # **Not swallowed.** The subscriber's own unsubscribe
                        # runs inside this cancellation, so anything else
                        # arriving here is a ``PubSub`` that did not close —
                        # a leaked connection rather than a stream ending.
                        logger.warning(
                            "the live channel's subscription did not close cleanly",
                            extra={"conversation_id": str(opening.conversation_id)},
                            exc_info=True,
                        )

    async def _what_changed(
        self, conversation_id: UUID, *, reader_id: UUID, showing: tuple[UUID, ...]
    ) -> Typing | None:
        """The frame this check produced, or ``None`` if the answer is unmoved.

        **Off the loop because it is the other half of it.** What is left in
        ``follow`` is the nudge relay ``docs/adr/0147`` wrote, plus one call; the
        read, the filter and the comparison are one question — *has who is typing
        changed for this reader* — and they belong together where the loop's four
        exits are not in the way.

        **The reader is filtered here**, because the store's answer is the same
        for everybody following the room and only a stream knows whose it is; and
        the order is ``Typing.of``'s, so two frames about the same two people are
        the same bytes (``docs/adr/0105``).
        """

        typing = await self._typists.who_is_typing(conversation_id)
        frame = Typing.of(conversation_id, typing - {reader_id})
        return None if frame.player_ids == showing else frame
