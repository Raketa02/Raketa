"""The push channel: one message, one queue, and one line per player.

ADR-0062, ADR-0065 and ADR-0067. Three things live here — the write that records
where a phone is, the send that decides whether a player is told anything at
all, and the batch that runs the queue on the tick the outbox already runs.

**Its own queue, and not a delayed outbox row.** A send is not a change leaving
the building: the offer that caused it is already written and already true, and
the outbox exists so a support agent can explain a game somebody *paid for*. The
queue is one row per player, coalesced, which is *one live message per player*
expressed on this side of the wire — a second dispatch reaching the same person
before her send runs is one send and not two.

**The ranking is over the whole live set, every time.** ADR-0065 is explicit
that it is not within one dispatch: a chosen seat arriving while a standby seat
holds the line must never take the line, so the send re-reads everything she
holds and ranks it whole, rather than looking at what the dispatch that woke it
happened to write.

**Nothing here is told what changed.** The queue row says *this player may have
something new*, and everything else is re-derived from the offers found now —
``RunCascade``'s *"a dispatch is a look, not an instruction"*, applied to the
job downstream of it. So a send that runs late tells the truth late rather than
telling a stale truth, and running one twice sends nothing the first did not,
because the second finds the named seat unchanged.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from uuid import UUID

from app.application.ports import UnitOfWork
from app.kernel import Clock, Instant, Minutes, instant

from app.modules.now.application.compose_offers import is_still_there
from app.modules.now.domain.ports import (
    OfferedSeats,
    PushDevices,
    PushLines,
    PushSender,
)
from app.modules.now.domain.push import (
    LiveLine,
    Platform,
    PushDevice,
    PushMessage,
    TimeSensitiveSetting,
    message_due,
    message_for,
    named_seat,
)

logger = logging.getLogger(__name__)

#: How many players' lines one tick considers. ``CASCADE_BATCH_SIZE``'s number
#: and its argument: a ceiling on the work a single look does, never a promise
#: about latency, because whatever is left is still due next tick.
PUSH_BATCH_SIZE = 100

#: How long the named seat is from the reader, in minutes. **Nothing can supply
#: it**: a distance is measured from the optional anchor ADR-0063 defines, no
#: screen asks for one, and ``ClubSnapshot.travel_minutes`` is a sentinel chosen
#: to be provably unable to move a score (``Raketa02/Raketa#129``).
#:
#: It is passed rather than dropped for the reason ``OfferKind`` keeps a name it
#: never writes: ADR-0062 fixes the copy as *sport, time and travel time*, and a
#: clause that exists is a clause that turns on with a value rather than with a
#: release.
NO_TRAVEL: Minutes | None = None


class SendOutcome(str, Enum):
    """What one player's send did. Returned for the log and the tests."""

    #: A message went out and her line now names a different match.
    SENT = "sent"
    #: The named seat did not change. **Nothing is sent on either platform**
    #: (ADR-0067), so the count she is looking at undercounts until it does.
    UNCHANGED = "unchanged"
    #: Nothing of hers is live any more. Her lock screen is left exactly as it
    #: is: past-tense wording means the line she holds has not become false.
    NOTHING_LIVE = "nothingLive"
    #: No phone has told us where she is. Her line is left naming whatever it
    #: named — which is nothing — so the day she registers one she is told.
    UNREACHABLE = "unreachable"


@dataclass(frozen=True)
class RegisterDeviceCommand:
    """*Reach me here.* One phone, its platform, and what its settings said.

    The moment is not on it: **when** a phone told us is the server's fact, like
    every other instant in this app, and a client-supplied one would be a clock
    the product does not control deciding which of two registrations is newer.
    """

    player_id: UUID
    token: str
    platform: Platform
    time_sensitive: TimeSensitiveSetting


class RegisterDevice:
    """Record where a player can be reached. **Nothing branches on the setting.**

    ``timeSensitiveSetting`` is stored and read by nobody who decides anything
    (ADR-0065): the cascade does not demote a player who has revoked, because
    demoting her would quietly cost her seats as a punishment for a settings
    choice. It is observability — if a large fraction of players revoke, that
    record's central judgement was wrong, and this is the only way we would
    learn it.
    """

    def __init__(
        self, *, devices: PushDevices, uow: UnitOfWork, clock: Clock
    ) -> None:
        self._devices = devices
        self._uow = uow
        self._clock = clock

    async def execute(self, command: RegisterDeviceCommand) -> None:
        await self._devices.register(
            PushDevice(
                player_id=command.player_id,
                token=command.token,
                platform=command.platform,
                time_sensitive=command.time_sensitive,
                registered_at=instant(self._clock.now()),
            )
        )
        await self._uow.commit()


class SendTheLine:
    """One player: rank her live seats, and send only if the named one changed."""

    def __init__(
        self,
        *,
        lines: PushLines,
        offered: OfferedSeats,
        devices: PushDevices,
        sender: PushSender,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._lines = lines
        self._offered = offered
        self._devices = devices
        self._sender = sender
        self._uow = uow
        self._clock = clock

    async def execute(self, line: LiveLine) -> SendOutcome:
        """Everything one owed send may do, and the four ways it ends.

        **Liveness is asked here and by the same expression the region asks it
        with.** An offer is a fact about the past; whether the seat is still
        there is a question about the match, asked at the instant something is
        composed from it. A line naming a seat somebody else has taken is not a
        lie — the wording is past tense — but naming one *first* would spend the
        interruption on the seat least worth racing for.
        """

        now = instant(self._clock.now())
        live = [
            seat
            for seat in await self._offered.for_player(
                player_id=line.player_id, now=now
            )
            if is_still_there(seat, now=now)
        ]
        named = named_seat(live)
        if named is None:
            await self._settle(line)
            return SendOutcome.NOTHING_LIVE

        devices = await self._devices.for_player(line.player_id)
        messages = [
            message_for(
                device,
                named=named,
                others=len(live) - 1,
                # The one clause the platform cannot fill. See `NO_TRAVEL`.
                travel=NO_TRAVEL,
            )
            for device in devices
            if message_due(
                named=named, holding=line.named_match_id, platform=device.platform
            )
        ]
        if not messages:
            await self._settle(line)
            # A player with no phone at all is a different fact from a player
            # whose line already names this seat, and the two must not collapse:
            # the first is somebody the channel has never reached, and her line
            # is left naming nothing so that her first message is still owed the
            # day she registers a token.
            return (
                SendOutcome.UNREACHABLE if not devices else SendOutcome.UNCHANGED
            )

        await self._sender.send(messages)
        # Written **after** the send, so a transport that raised leaves the row
        # due and the next tick tries again. The direction the failure points in
        # is a message sent twice rather than a seat nobody hears about — and a
        # second message carrying the same collapse id replaces the first rather
        # than stacking beside it, which is the whole reason that id exists.
        #
        # It is a compare-and-set against the line this send **read**, so a
        # dispatch that told her about something while the message was in flight
        # is still owed a send afterwards rather than having its debt cleared by
        # a run that never saw its offer.
        await self._lines.replaced(
            line, named_match_id=named.match_id, at=now
        )
        await self._uow.commit()
        _log_sent(line.player_id, messages)
        return SendOutcome.SENT

    async def _settle(self, line: LiveLine) -> None:
        """Clear the debt and leave her lock screen exactly as it is."""

        await self._lines.settled(line)
        await self._uow.commit()


class PushBatch:
    """Every owed send at this instant, run once each.

    The **fourth** job on the event worker's one tick, and last of the four for
    the reason the cascade is third: the jobs above decide what is *true* — a
    court given back, a claim reaped, a seat offered — and this one is the only
    thing in the product that makes a phone light up. A message composed before
    the dispatch that caused it would be a message about a seat that did not
    exist yet; one composed after a wake is a message about the match as it now
    stands.

    **One failed send does not stop the batch**, on ``CascadeBatch``'s rule and
    with its rollback: two players have nothing to do with each other, and a
    session left holding a failed statement fails every send after it.
    """

    def __init__(
        self,
        *,
        lines: PushLines,
        send: SendTheLine,
        uow: UnitOfWork,
        clock: Clock,
        batch_size: int = PUSH_BATCH_SIZE,
    ) -> None:
        self._lines = lines
        self._send = send
        self._uow = uow
        self._clock = clock
        self._batch_size = batch_size

    async def execute(self, *, worker_id: str) -> int:
        """One tick's worth of sends. ``worker_id`` names who took them.

        ``TickWork``'s shape. There are no leases, for ``CascadeBatch``'s
        reason turned around: a send that runs twice sends nothing the second
        time, because the second run finds the named seat unchanged.
        """

        now: Instant = instant(self._clock.now())
        owed = await self._lines.due(now=now, limit=self._batch_size)
        ran = 0
        for line in owed:
            try:
                await self._send.execute(line)
            except Exception:  # noqa: BLE001 — one phone must not stop the tick
                await self._uow.rollback()
                logger.exception(
                    "push send failed", extra={"player": str(line.player_id)}
                )
                continue
            ran += 1
        if ran:
            logger.info(
                "push sends taken", extra={"worker_id": worker_id, "taken": ran}
            )
        return ran


def _log_sent(player_id: UUID, messages: list[PushMessage]) -> None:
    """What went out, without the body and without the token.

    The body names a sport and an hour and the token addresses a phone; neither
    belongs in an operational log, and a log line is a copy of a lock screen
    that outlives it.
    """

    logger.info(
        "push line replaced",
        extra={
            "player": str(player_id),
            "devices": len(messages),
            "platforms": sorted(
                {message.platform.value for message in messages}
            ),
        },
    )
