"""**The room is told, through the outbox, by contexts that do not know it
exists.**

``docs/adr/0146`` §5. ``challenges``, ``games`` and ``plans`` publish; this
subscribes; and no publisher gains a line of code about a conversation. That
ignorance is the whole of the argument — the moment ``challenges`` knows a room
exists, the two ship as one thing.

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
(``source_event_id`` on the aggregate); a game is noted at most once; and a room
is destroyed at most once, because a room that is not there is the state the
destruction asks for. A redelivery therefore lands the same state and records
nothing, which is this repository's existing idempotency language applied to
delivery rather than to a client.

**What is refused, and why, is in ``telling.py``** — as a table, so the six the
prose says publish nothing are named in one place a test can walk.

**Two arms write nothing into the room and take the room away.** A withdrawal
**destroys** it (``docs/adr/0153`` §2), and so does the game being called off
(``docs/adr/0165`` §3) — a departure that leaves one player on a game calls it
off with no withdrawal beside it. The tellings that draw the least are the ones
with the largest effect — which is why their rows in ``telling.py`` reach the
room while refusing a line, and why a reader who took *refused* to mean *not
delivered* would leave every withdrawn court a readable room for ever.

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
from app.kernel import Instant, instant, minute_of_day
from app.modules.challenges.domain.events import (
    ChallengeOpenedFromMutualInterest,
    ChallengeWithdrawn,
    SeatAccepted,
    SeatDeclined,
    SeatLapsed,
    SeatLeft,
    SeatsInvited,
)
from app.modules.conversations.domain.conversation import Conversation
from app.modules.conversations.application.telling import line_drawn_by, line_for
from app.modules.conversations.domain.entries import (
    COUNT,
    DEPARTURE,
    VALUE,
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
from app.modules.games.domain.events import GameCalledOff, GamePlanned, GamePlayed
from app.modules.plans.domain.events import (
    DayRecorded,
    HourRecorded,
    PlaceRecorded,
    PlanLocked,
)
from app.modules.plans.domain.slots import as_wall_time
from app.shared.domain import DomainEvent


@final
class TellTheRoom:
    """One handler for every event this room is told about.

    One class rather than one per event, because they share a single shape —
    *find the room this is about, and either open it or write one line into it* —
    and the interesting differences are three lines each. A class each would put
    the shared shape in ten places, which is where a redelivery gets handled nine
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
            await self._mutual(event, context)
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
        elif isinstance(event, (SeatDeclined, SeatLapsed, SeatLeft)):
            # **One code, with declined, lapsed or left as a value.** *That seat
            # is open again* is the same news each way, and a lapse is still not
            # a decline — the three facts stay apart in the value rather than in
            # a second code, which is what keeps *answers challenges* measurable
            # one layer up. A departure from a game (``docs/adr/0162``) is the
            # one whose actor was a member until this very line; membership is
            # derived, so the read has already dropped them by the time the
            # line is drawn, and ``people`` names them all the same.
            await self._line_in(
                event.challenge_id,
                event,
                actor_id=event.player_id,
                values={DEPARTURE: _departure_of(event).value},
                context=context,
            )
        elif isinstance(event, ChallengeWithdrawn):
            await self._withdrawn(event)
        elif isinstance(event, GameCalledOff):
            await self._called_off(event)
        elif isinstance(event, GamePlanned):
            await self._note_game(event)
        elif isinstance(event, GamePlayed):
            await self._said_they_played(event, context)
        elif isinstance(event, (PlaceRecorded, DayRecorded, HourRecorded)):
            await self._a_slot_was_recorded(event, context)
        elif isinstance(event, PlanLocked):
            await self._the_plan_was_locked(event, context)

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

    async def _mutual(
        self, event: ChallengeOpenedFromMutualInterest, context: DeliveryContext
    ) -> None:
        """Two yeses met. **The mutual is the opening, and on a doubles court it
        also says it is half a game** (``docs/adr/0169`` §8).

        Both seats are accepted from birth, so there was never a moment with one
        person in the room for a membership line to be about — a singles mutual
        opens the room and writes nothing. A doubles mutual seats the pair on
        **one side** with a whole side still to fill, and nothing in the room
        says so; that room is born with ``SIDE_FORMED`` at ``seq`` 1, which
        names no actor because it is about both of them, and carries no values
        because the client owns the words.

        **Whether the line is drawn is the table's decision and not this
        arm's**: ``line_drawn_by`` runs the row's own condition — the court is
        a doubles one, read through ``challenges``' ``seats_per_side`` off the
        event's sport — so ``telling.py`` and this handler cannot come to two
        answers about the one row where they could. It is not read off
        ``ArrangingCourt``, which answers ``None`` for a challenge this context
        cannot be told about — then there is no room, and nothing is written.

        ***Born with* is literal: the opening and the line are one save.** The
        obvious shape — open, then ``_line_in`` — re-reads the room through the
        locked ``for_challenge`` a moment after ``save`` added its row, and the
        worker's session does not autoflush (``app/infrastructure/database/
        session.py``), so that read finds nothing and the line is dropped
        without a trace — while the suite's own session autoflushes and passes.
        So the line is recorded on the room the opening built, before the one
        save that writes both, and a second lookup is never made.

        **Idempotent on both halves.** A redelivery finds the room already open
        and the line already told by this outbox row, so the same row twice
        lands one room and one line — and nudges again with an unchanged
        ``last_seq``, which every phone already holding it ignores.
        """

        room = await self._conversations.for_challenge(event.challenge_id)
        opened_now = room is None
        if room is None:
            room = await self._opening(event.challenge_id, event.occurred_at)
            if room is None:
                return
        code = line_drawn_by(event)
        if code is not None:
            await self._write_line(
                room,
                code=code,
                actor_id=None,
                values={},
                source_event_id=context.event_id,
                occurred_at=instant(event.occurred_at),
            )
        elif opened_now:
            await self._conversations.save(room)

    async def _open(self, challenge_id: UUID, occurred_at: datetime) -> None:
        """Open the room, and **ask whether it is already about a game.**

        **A room is opened once per challenge and a fill continues it**
        (``docs/adr/0164`` §6). A half-built court whose room is still standing
        can be filled for as long as the challenge stands (``docs/adr/0150``),
        and the acceptance that follows finds the room already there and writes
        its line into the backlog the others have been reading — a room without
        a game lives exactly as long as its challenge, so there is no ending a
        later acceptance could have arrived after. A *withdrawn* challenge
        cannot reach here at all — it is ``ENDED``, so ``Challenge.invite``
        refuses and no further acceptance exists to deliver. What does reach here
        with no room to find is the **first** acceptance, which is the opening.

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
        opened = await self._opening(challenge_id, occurred_at)
        if opened is not None:
            await self._conversations.save(opened)

    async def _opening(
        self, challenge_id: UUID, occurred_at: datetime
    ) -> Conversation | None:
        """The room this challenge opens, **built and not yet saved** — so the
        caller can put into it whatever it is born with before the one save.

        ``None`` for a challenge this context cannot be told about: opening a
        room without a sport would put a row in the list that no client can
        draw, so nothing is opened and the next telling opens it.
        """

        sport = await self._arranging.sport_of(challenge_id)
        if sport is None:
            return None
        opened = Conversation.opened(
            conversation_id=uuid4(),
            challenge_id=challenge_id,
            sport=sport,
            occurred_at=instant(occurred_at),
        )
        game_id = await self._played.game_of(challenge_id)
        if game_id is not None:
            opened.note_game(game_id=game_id, occurred_at=instant(occurred_at))
        return opened

    # -- being closed ------------------------------------------------------

    async def _withdrawn(self, event: ChallengeWithdrawn) -> None:
        """Whoever held the exit ended it. **The room is destroyed, and writes
        no line** — whether or not it already holds its game (``docs/adr/0163``).

        ``docs/adr/0153`` §2. There is nobody left to read a line — the news is on
        the challenge screen — and this is the only arm here whose whole effect is
        that the room stops existing.

        **No nudge, and that is not an omission.** A nudge says *the room is now
        this long*, and there is no room to be a length; a phone with the screen
        open finds ``conversation_not_found`` on its next fetch, which is the same
        answer it would get from the sweep and from a room that never existed.

        A room that is not there is a redelivery, a mutual whose challenge was
        withdrawn before anybody accepted, or a challenge this context cannot be
        told about — and all three want exactly nothing done.

        **A destroyed room cannot be re-opened behind this**, and the reason is
        the queue rather than a tombstone. An opening is a delivery of the
        acceptance that preceded the withdrawal, and the outbox is drained in
        ``(created_at, id)`` order — so a redelivered acceptance is fetched
        before this row, not after it. A tombstone would be the alternative, and
        it would be a stored fact about a thing whose whole point is that nothing
        of it survives.
        """

        room = await self._conversations.for_challenge(event.challenge_id)
        if room is None:
            return
        await self._conversations.destroy(room.conversation_id)

    async def _called_off(self, event: GameCalledOff) -> None:
        """The game this room was for is called off. **The room is destroyed,
        and writes no line** (``docs/adr/0165`` §3) — the withdrawal's arm,
        reached through the game.

        A call-off arrives with a withdrawal beside it (``docs/adr/0163``) or
        alone, told by the departure that left one player on the court. Beside
        a withdrawal, whichever of the two is delivered first destroys the room
        and this finds nothing; alone, this is the only telling that will. A
        room that is not there is that redelivery, or a game this context was
        never told about, and both want exactly nothing done. No nudge, for the
        withdrawal's reason: there is no room to be a length.

        **Found through the game, and the room always knows it by now.** A
        call-off is written in a strictly later transaction than the game's
        opening — a seat has to have been vacated first — so by the time this
        is delivered the room has either been told its game or was never
        opened at all.
        """

        room = await self._directory.for_game(event.game_id)
        if room is None:
            return
        await self._conversations.destroy(room.conversation_id)

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

    # -- being told about the plan ----------------------------------------

    async def _a_slot_was_recorded(
        self,
        event: PlaceRecorded | DayRecorded | HourRecorded,
        context: DeliveryContext,
    ) -> None:
        """One slot, one line, and the value is the only thing that travels.

        **Found through the challenge**, which is what the ``challenge_id`` on
        all four plan events buys (``docs/adr/0164`` §1): a plan is the
        challenge's and is drawn in the room from its opening, so the room is
        the one the challenge opened, whether or not a game exists yet.

        A room that is not there is a **safe drop and not a coin flip**. A plan
        is written only by somebody holding an accepted seat, and the
        ``SeatAccepted`` that put them there — the room's own opening, or a
        later yes into a room already open — was published in a strictly
        earlier transaction, so by the time this arrives the room has been
        opened or was destroyed since, and there is nothing to hang the line on
        and nothing to retry.

        **Three codes and one shape.** Which slot it was is the code's business;
        what was written is the value's; and *set* against *changed* is nobody's,
        because they are the same fact told twice.
        """

        room = await self._conversations.for_challenge(event.challenge_id)
        if room is None:
            return
        await self._write_line(
            room,
            code=line_for(event),
            actor_id=event.recorded_by,
            values={VALUE: _slot_value(event)},
            source_event_id=context.event_id,
            occurred_at=instant(event.occurred_at),
        )

    async def _the_plan_was_locked(
        self, event: PlanLocked, context: DeliveryContext
    ) -> None:
        """Somebody agreed the plan. **One line, and it carries no value.**

        ``docs/adr/0155``. The value is the three slots and the room already has
        a line for each of them, so a value here would be the second place they
        are true and the first thing to disagree with the slot line above it
        after a later move. It is the only plan line with an empty ``values``.

        Found through the challenge and dropped safely when there is no room, on
        the slot arm's reasoning exactly — a plan is locked only by somebody
        holding an accepted seat, and that acceptance was published first.
        """

        room = await self._conversations.for_challenge(event.challenge_id)
        if room is None:
            return
        await self._write_line(
            room,
            code=line_for(event),
            actor_id=event.locked_by,
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


def _slot_value(
    event: PlaceRecorded | DayRecorded | HourRecorded,
) -> str:
    """What a slot line carries. **A value, never a sentence** (``docs/adr/0022``).

    The place as it was typed, the day as an ISO date, and the hour as a clock
    face — each a thing the client formats rather than a thing it prints.

    **The hour is spelled by the Plan and never here.** It is stored as a minute
    of the local day, and this calls that context's own inverse rather than
    formatting one: the spelling belongs to whoever owns the value, and a second
    ``divmod(minute, 60)`` in this file is how a line and the wire start
    disagreeing about 18:00.
    """

    if isinstance(event, PlaceRecorded):
        return event.place
    if isinstance(event, DayRecorded):
        return event.day
    return as_wall_time(minute_of_day(event.minute_of_day)).isoformat("minutes")


def _departure_of(event: SeatDeclined | SeatLapsed | SeatLeft) -> SeatDeparture:
    """Which of the three ways a seat opens this event is."""

    if isinstance(event, SeatDeclined):
        return SeatDeparture.DECLINED
    if isinstance(event, SeatLapsed):
        return SeatDeparture.LAPSED
    return SeatDeparture.LEFT
