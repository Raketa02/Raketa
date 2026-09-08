"""**The room is told, through the outbox, by contexts that do not know it
exists.**

``docs/adr/0146`` §5. ``challenges`` and ``games`` publish; this subscribes; and
neither publisher gains a line of code about a conversation. That ignorance is
the whole of the argument — the moment ``challenges`` knows a room exists, the
two ship as one thing.

**It is a subscriber and never a participant in anybody's transaction.** The two
alternatives were refused by name: an *inline port* — the shape ``challenges``
uses to open a game — would put the room inside the acceptance's transaction, and
a *read at open* would put three contexts' event vocabularies in a read path and
interleave messages with lines by timestamp, which is an ordering nobody owns.

**The price is stated rather than hidden**: a room can be wrong about the world
for as long as the outbox takes. Somebody accepts, the game opens, and the line
saying so lands a poll later. Nothing in a room is a gate and no act is refused on
the strength of a system line, which is what makes that the right price here.

**Every write here is idempotent**, because the outbox is at-least-once by
construction. A room is opened at most once per challenge (the repository's
locked ``for_challenge`` read); a line is written at most once per **outbox row**
(``source_event_id`` on the aggregate); a game is noted at most once. A
redelivery therefore lands the same state and records nothing, which is this
repository's existing idempotency language applied to delivery rather than to a
client.

**What is refused, and why, is in ``telling.py``** — as a table, so the six the
prose says publish nothing are named in one place a test can walk.

**A line nudges the room and an opening does not**, which is the nudge's own
shape rather than a rule about tellings (``docs/adr/0147`` §3). A frame says *the
room is now this long*; the opening and the noting of a game move no ``seq``, so
a frame about either would send every phone to the read path to be told what it
already holds. Everything a client draws from those two — the room's existence,
its game, its *Details* door — arrives on the ordinary list and detail reads.

**The nudge rides ahead of the delivery's own commit, and this is the one place
that ordering is not guaranteed.** ``send_message`` publishes strictly after its
own commit and says so; nothing here commits at all — the transaction is
``EventBatch``'s, closed by the ``published_at`` that marks the row delivered — so
the publish precedes the commit by the width of one ``UPDATE``.

Two cases, and only one of them is a real window. If the mark **fails**, the row
is redelivered, the line is re-recorded idempotently and the nudge goes again:
the outbox repairs it, and this is the ordinary failure. If it **succeeds**, a
phone that fetched inside the gap would read the room as it stood a moment ago —
and, for a lone system line, **nothing would nudge again**, so it would stay
stale until the fifteen-minute reconnect. What makes that unobservable rather
than merely unlikely is the shape of the gap: it is in-process and microseconds
wide, while the repair fetch it would have to beat is a network round trip that
has not been issued yet when the ``UPDATE`` lands.

**It is stated rather than closed, and the alternative is named.** Closing it
means a post-commit hook through ``EventBatch`` — the one loop every context
shares — so that a conversation's vocabulary, or a general deferral protocol
shaped by it, lands in the middle of the outbox. That is a real cost against a
window nothing can observe, and it is the trade this file takes deliberately.
"""

from __future__ import annotations

from typing import final
from datetime import datetime
from uuid import UUID, uuid4

from app.application.events import DeliveryContext
from app.kernel import Instant, instant
from app.modules.challenges.domain.events import (
    ChallengeOpenedFromMutualInterest,
    SeatAccepted,
    SeatDeclined,
    SeatLapsed,
    SeatsInvited,
)
from app.modules.conversations.domain.conversation import Conversation
from app.modules.conversations.application.telling import line_for
from app.modules.conversations.domain.entries import (
    COUNT,
    DEPARTURE,
    SeatDeparture,
    SystemLineCode,
)
from app.modules.conversations.domain.live import Nudge, NudgePublisher
from app.modules.conversations.domain.ports import (
    ArrangingCourt,
    ConversationDirectory,
    ConversationRepository,
    PlayedCourt,
)
from app.modules.games.domain.events import GamePlanned, GamePlayed
from app.shared.domain import DomainEvent


@final
class TellTheRoom:
    """One handler for every event this room is told about.

    One class rather than seven, because the seven share a single shape — *find
    the room this is about, and either open it or write one line into it* — and
    the interesting differences are three lines each. Seven classes would put the
    shared shape in seven places, which is where a redelivery gets handled six
    times.
    """

    def __init__(
        self,
        *,
        conversations: ConversationRepository,
        directory: ConversationDirectory,
        arranging: ArrangingCourt,
        played: PlayedCourt,
        nudges: NudgePublisher,
    ) -> None:
        self._conversations = conversations
        self._directory = directory
        self._arranging = arranging
        self._played = played
        self._nudges = nudges

    async def __call__(self, event: DomainEvent, context: DeliveryContext) -> None:
        """Deliver one event to the room it is about.

        **Nothing here commits.** The transaction is the outbox delivery's, and
        ``EventBatch`` closes it with the ``published_at`` that says this event
        was delivered — so a line and the mark saying it was written stand or
        fall together.
        """

        if isinstance(event, ChallengeOpenedFromMutualInterest):
            # **The mutual is the opening and writes no line.** Both seats are
            # accepted from birth, so there was never a moment with one person
            # in the room for a line to be about.
            await self._open(event.challenge_id, event.occurred_at)
        elif isinstance(event, SeatAccepted):
            await self._accepted(event, context)
        elif isinstance(event, SeatsInvited):
            await self._line_in(
                event.challenge_id,
                event,
                actor_id=event.invited_by,
                values={COUNT: str(len(event.newly_invited))},
                context=context,
            )
        elif isinstance(event, (SeatDeclined, SeatLapsed)):
            # **One code, with declined-or-lapsed as a value.** *That seat is
            # open again* is the same news either way, and a lapse is still not
            # a decline — the two facts stay apart in the value rather than in a
            # second code, which is what keeps *answers challenges* measurable
            # one layer up.
            await self._line_in(
                event.challenge_id,
                event,
                actor_id=event.player_id,
                values={
                    DEPARTURE: (
                        SeatDeparture.DECLINED.value
                        if isinstance(event, SeatDeclined)
                        else SeatDeparture.LAPSED.value
                    )
                },
                context=context,
            )
        elif isinstance(event, GamePlanned):
            await self._note_game(event)
        elif isinstance(event, GamePlayed):
            await self._said_they_played(event, context)

    # -- opening ----------------------------------------------------------

    async def _accepted(self, event: SeatAccepted, context: DeliveryContext) -> None:
        """The first acceptance opens the room; every later one writes a line.

        **One rule, and it is the same one three codes share.** The first
        acceptor is a founding member, visible in membership rather than
        announced in a backlog nobody could have been reading.
        """

        room = await self._conversations.for_challenge(event.challenge_id)
        if room is None:
            await self._open(event.challenge_id, event.occurred_at)
            return
        await self._write_line(
            room,
            code=line_for(event),
            actor_id=event.player_id,
            values={},
            source_event_id=context.event_id,
            occurred_at=instant(event.occurred_at),
        )

    async def _open(self, challenge_id: UUID, occurred_at: datetime) -> None:
        """Open the room, and **ask whether it is already about a game.**

        That second half is not belt and braces. The accept that fills the last
        seat writes ``SeatAccepted`` and ``GamePlanned`` in one transaction, and
        the outbox orders by ``(created_at, id)`` where ``created_at`` is
        transaction-start time — identical for both — so the tie-break is a
        minted uuid and the delivery order is a coin flip
        (``docs/adr/0097``). Whichever arrives first, the room ends up the same:
        ``GamePlanned`` first drops (there is nothing to tell), and the opening
        that follows finds the game itself.
        """

        room = await self._conversations.for_challenge(challenge_id)
        if room is not None:
            # A redelivery, or a mutual whose two seats arrived as two events.
            return
        sport = await self._arranging.sport_of(challenge_id)
        if sport is None:
            # A challenge this context cannot be told about. Opening a room
            # without a sport would put a row in the list that no client can
            # draw, so nothing is opened and the next telling opens it.
            return
        opened = Conversation.opened(
            conversation_id=uuid4(),
            challenge_id=challenge_id,
            sport=sport,
            occurred_at=instant(occurred_at),
        )
        game_id = await self._played.game_of(challenge_id)
        if game_id is not None:
            opened.note_game(game_id=game_id, occurred_at=instant(occurred_at))
        await self._conversations.save(opened)

    # -- being told about the game ----------------------------------------

    async def _note_game(self, event: GamePlanned) -> None:
        """The line-up completed. **Drawn, not announced** — and a safe drop.

        A room that does not exist yet is one whose opening acceptance has not
        been delivered, which is the coin flip ``_open`` answers: that opening
        reads the game for itself, so dropping here loses nothing.
        """

        room = await self._conversations.for_challenge(event.challenge_id)
        if room is None:
            return
        room.note_game(game_id=event.game_id, occurred_at=instant(event.occurred_at))
        await self._conversations.save(room)

    async def _said_they_played(
        self, event: GamePlayed, context: DeliveryContext
    ) -> None:
        room = await self._directory.for_game(event.game_id)
        if room is None:
            # **Not the coin flip above.** ``GamePlayed`` is written in a strictly
            # later transaction than ``GamePlanned``, so by the time this is
            # delivered the room either knows its game or was never opened at
            # all — a challenge this context cannot be told about. There is
            # nothing to hang the line on and nothing to retry.
            return
        await self._write_line(
            room,
            code=line_for(event),
            actor_id=event.said_by,
            values={},
            source_event_id=context.event_id,
            occurred_at=instant(event.occurred_at),
        )

    # -- the shared shape --------------------------------------------------

    async def _line_in(
        self,
        challenge_id: UUID,
        event: DomainEvent,
        *,
        actor_id: UUID | None,
        values: dict[str, str],
        context: DeliveryContext,
    ) -> None:
        """Write one line, **only when there was already a room to write it in**.

        The code comes from ``telling.py`` rather than from this call site, so
        the table a test walks and the line that ships cannot part company.
        """

        room = await self._conversations.for_challenge(challenge_id)
        if room is None:
            return
        await self._write_line(
            room,
            code=line_for(event),
            actor_id=actor_id,
            values=values,
            source_event_id=context.event_id,
            occurred_at=instant(event.occurred_at),
        )

    async def _write_line(
        self,
        room: Conversation,
        *,
        code: SystemLineCode,
        actor_id: UUID | None,
        values: dict[str, str],
        source_event_id: UUID,
        occurred_at: Instant,
    ) -> None:
        """Record one line, save it, and nudge the room. **The three appends
        share this**, so a fourth cannot arrive live-less by forgetting a call.

        **A redelivery nudges too**, and does not have to be told apart from a
        first delivery to do so: ``record_line`` answers the line that already
        stands and records nothing, and the nudge that follows carries the room's
        unchanged ``last_seq`` — true, and a no-op to every phone already holding
        it.
        """

        room.record_line(
            code=code,
            actor_id=actor_id,
            values=values,
            source_event_id=source_event_id,
            occurred_at=occurred_at,
        )
        await self._conversations.save(room)
        await self._nudges.nudge(Nudge.about(room))
