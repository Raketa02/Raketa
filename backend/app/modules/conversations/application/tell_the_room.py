"""**The room is told, through the outbox, by a context that does not know it
exists.**

``docs/adr/0146`` §5. ``games`` publishes; this subscribes; and no publisher
gains a line of code about a conversation. That ignorance is the whole of the
argument — the moment ``games`` knows a room exists, the two ship as one thing.

**A room is opened only by a booked game** (#541, #575). A booking's yeses are
silent and open nothing, so the game the booking opened is the opening: its
``GamePlanned``, with the hour on it, opens the room already about the game,
filed under the booking. A game with no hour is one a challenge's line-up
completed into; nothing opens a room for it any more.

**It is a subscriber and never a participant in anybody's transaction.** The two
alternatives were refused by name: an *inline port* would put the room inside
the booking's transaction, and a *read at open* would put another context's
event vocabulary in a read path and interleave messages with lines by
timestamp, which is an ordering nobody owns.

**The price is stated rather than hidden**: a room can be wrong about the world
for as long as the outbox takes. A game is booked, and its room lands a poll
later. Nothing in a room is a gate and no act is refused on the strength of a
system line, which is what makes that the right price here.

**Every write here is idempotent**, because the outbox is at-least-once by
construction. A room is opened at most once per booking (the repository's
locked ``for_booking`` read); a line is written at most once per **outbox row**
(``source_event_id`` on the aggregate); a game is noted at most once; and a room
is destroyed at most once, because a room that is not there is the state the
destruction asks for. A redelivery therefore lands the same state and records
nothing.

**What is refused, and why, is in ``telling.py``** — as a table, so every event
that publishes nothing is named in one place a test can walk.

**One arm writes nothing into the room and takes the room away**: the game
being called off destroys it (``docs/adr/0165`` §3). The telling that draws the
least has the largest effect — which is why its row in ``telling.py`` reaches
the room while refusing a line, and why a reader who took *refused* to mean *not
delivered* would leave every called-off game a readable room for ever.

**A line nudges the room and an opening does not**, which is the nudge's own
shape rather than a rule about tellings (``docs/adr/0147`` §3). A frame says *the
room is now this long*; the opening moves no ``seq``, so a frame about it would
send every phone to the read path to be told what it already holds. Everything a
client draws from it — the room's existence, its game — arrives on the ordinary
list and detail reads.

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
from uuid import UUID, uuid4

from app.application.events import DeliveryContext
from app.kernel import Instant, Sport, instant
from app.modules.conversations.application.telling import line_for
from app.modules.conversations.domain.conversation import Conversation
from app.modules.conversations.domain.entries import SystemLineCode
from app.modules.conversations.domain.live import Nudge, NudgePublisher
from app.modules.conversations.domain.ports import (
    ConversationDirectory,
    ConversationRepository,
)
from app.modules.games.domain.events import GameCalledOff, GamePlanned, GamePlayed
from app.shared.domain import DomainEvent


@final
class TellTheRoom:
    """One handler for every event this room is told about.

    One class rather than one per event, because they share a single shape —
    *find the room this is about, and either open it, write one line into it,
    or take it away* — and the differences are three lines each.
    """

    def __init__(
        self,
        *,
        conversations: ConversationRepository,
        directory: ConversationDirectory,
        nudges: NudgePublisher,
    ) -> None:
        self._conversations = conversations
        self._directory = directory
        self._nudges = nudges

    async def __call__(self, event: DomainEvent, context: DeliveryContext) -> None:
        """Deliver one event to the room it is about.

        **Nothing here commits.** The transaction is the outbox delivery's, and
        ``EventBatch`` closes it with the ``published_at`` that says this event
        was delivered — so a line and the mark saying it was written stand or
        fall together.
        """

        if isinstance(event, GamePlanned):
            await self._open(event)
        elif isinstance(event, GamePlayed):
            await self._said_they_played(event, context)
        elif isinstance(event, GameCalledOff):
            await self._called_off(event)

    # -- opening ----------------------------------------------------------

    async def _open(self, event: GamePlanned) -> None:
        """A game was booked. **Its room opens, already about it.**

        The mechanics §14.3: *the chat opens when the game is booked*. A
        booking has no acceptances to open a room by — its yeses are silent —
        so the game it opened is the opening, and the room is born about it,
        its hour on it, its members the game's line-up. It is filed under the
        arrangement the game names, the booking, so a redelivery finds it and
        records nothing.

        **A game with no hour opens nothing.** It is one a challenge's line-up
        completed into, and nothing opens a room for that any more (#575).

        ***Born with* is literal: the opening and the game are one save.** The
        worker's session does not autoflush (``app/infrastructure/database/
        session.py``), so the room is built, told its game, and saved once —
        never opened, re-read and told.
        """

        if event.starts_at is None:
            return
        room = await self._conversations.for_booking(event.challenge_id)
        if room is None:
            room = Conversation.opened(
                conversation_id=uuid4(),
                booking_id=event.challenge_id,
                sport=Sport(event.sport),
                occurred_at=instant(event.occurred_at),
            )
        room.note_game(
            game_id=event.game_id,
            occurred_at=instant(event.occurred_at),
            starts_at=instant(event.starts_at),
        )
        await self._conversations.save(room)

    # -- being closed ------------------------------------------------------

    async def _called_off(self, event: GameCalledOff) -> None:
        """The game this room was for is called off. **The room is destroyed,
        and writes no line** (``docs/adr/0165`` §3).

        **No nudge, and that is not an omission.** A nudge says *the room is now
        this long*, and there is no room to be a length; a phone with the screen
        open finds ``conversation_not_found`` on its next fetch, which is the
        same answer it would get from the sweep and from a room that never
        existed.

        A room that is not there is a redelivery or a game this context never
        opened a room for, and both want exactly nothing done. **Found through
        the game, and the room always knows it by now**: a call-off is written
        in a strictly later transaction than the booking that opened the room.
        """

        room = await self._directory.for_game(event.game_id)
        if room is None:
            return
        await self._conversations.destroy(room.conversation_id)

    # -- being told about the game ----------------------------------------

    async def _said_they_played(
        self, event: GamePlayed, context: DeliveryContext
    ) -> None:
        room = await self._directory.for_game(event.game_id)
        if room is None:
            # ``GamePlayed`` is written in a strictly later transaction than
            # ``GamePlanned``, so by the time this is delivered the room either
            # knows its game or was never opened at all. There is nothing to
            # hang the line on and nothing to retry.
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
        """Record one line, save it, and nudge the room. **Every append shares
        this**, so a second cannot arrive live-less by forgetting a call.

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
