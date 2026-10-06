"""The Conversation aggregate — one room, its stream inside it, event-sourced.

**The place the people booked on one game talk about it.** Opened by the booked
game itself (#541, #575) and told about everything else by contexts that do not
know it exists (``docs/adr/0146``).

Three things about it are load-bearing and none is obvious from the code alone.

**Membership is nowhere in here.** It is derived from the record the room is
about — the game's **current** line-up — and a roster stored on this aggregate
would be the copy that decides who may read the messages and the first one to
go wrong. That rule lives in ``application/membership.py`` because it reads
another context, and this aggregate holds only the ids it is read against.

**The sequence is the aggregate's own fact and never the store's.** ``seq`` is
``last_seq + 1``, minted here and written under the conversation row's lock by
the repository (``docs/adr/0147`` §2) — not a Postgres sequence object, which is
documented not to be gapless, and not a timestamp, which ADR-0097 disqualified.
It is also **not the stream version**: the opening event has a version and no
``seq``, so the two part company at row one.

**Two acts here are idempotent, and each for its own reason.** A message repeats
on ``client_message_id`` because a paused send that resumes must not become two
bubbles; a system line repeats on ``source_event_id`` because the outbox is
at-least-once and a subscriber that writes has to recognise a redelivery. Both
answer with the entry that already stands and record nothing, which is this
repository's existing idempotency language.

**Nothing here stores a standing and nothing announces one.** There is no *Game
on* line: a booked game is announced on Home and its details, and a line saying
so would be a second place for a folded fact to be true.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping
from uuid import UUID

from app.kernel import Instant, Sport, instant, invariant
from app.modules.conversations.domain.entries import (
    Entry,
    Message,
    MessageText,
    SystemLine,
    SystemLineCode,
)
from app.modules.conversations.domain.events import (
    ConversationOpened,
    ConversationOpenedUnderAChallengeId,
    GameNoted,
    MessageSent,
    SystemLineRecorded,
)
from app.shared.domain import DomainEvent
from app.shared.domain.events import EventRecorder


@dataclass
class Conversation:
    """One purpose-bound room, rebuilt by folding its stream."""

    conversation_id: UUID
    #: The booking whose game opened this room — what the room is filed under,
    #: and what a client finds it by (#575). Every booked game carries it as the
    #: arrangement it was opened from, so the list read finds every room a
    #: player is in through the games they are on.
    booking_id: UUID
    #: The game this room is about. A booked game opens its room already about
    #: it, so this is set from the room's first save; ``None`` only on a room
    #: a challenge opened, which nothing opens any more and whose end has come.
    game_id: UUID | None
    #: The moment that game was booked. It is ``GamePlanned.occurred_at``, which
    #: **is** ``Game.planned_at`` (``docs/adr/0153`` §2) — carried on the telling
    #: this room already receives, so the room's own end costs no new event, no
    #: new field on the wire and no new telling.
    planned_at: Instant | None
    #: The hour the game is played (#541). Carried on the same telling as
    #: ``planned_at`` and read beside it: a booked game's room ends on its hour,
    #: not on a week from its booking.
    starts_at: Instant | None
    sport: Sport
    opened_at: Instant
    #: Every entry, oldest first. A room is destroyed within days of the evening
    #: it was arranging, so folding the whole stream is bounded by the room
    #: rather than by the platform — the difference ``docs/adr/0148`` §6 draws
    #: between a record and a room, applied to what a read costs.
    entries: tuple[Entry, ...]
    version: int = 0
    #: Which tellings this room has already folded, kept beside the entries
    #: rather than on them: a ``SystemLine`` is what a reader sees, and the
    #: outbox row that caused it is a fact about **delivery** rather than about
    #: the line. It is what makes a redelivery record nothing.
    _told_by: dict[UUID, int] = field(
        default_factory=dict, init=False, repr=False, compare=False
    )
    _events: EventRecorder = field(
        default_factory=EventRecorder, init=False, repr=False, compare=False
    )

    @property
    def id(self) -> UUID:
        """The stream id. **Minted, and carried on the opening event.**

        Its own id rather than the booking's (``docs/adr/0148`` §2): keying on
        the arrangement's id would foreclose a second kind of conversation, and
        a UUID costs one column.
        """

        return self.conversation_id

    @property
    def last_seq(self) -> int:
        """The count of what has landed here. **Zero in a room with no entries.**

        Folded from the entries rather than stored on the aggregate, so there is
        one place in the domain it is true. The column of the same name on the
        conversation row is the *allocator's* copy — what the lock is taken on
        and what the live channel publishes without a second read
        (``docs/adr/0147`` §2) — and the repository writes it from here.
        """

        return self.entries[-1].seq if self.entries else 0

    @property
    def last_entry(self) -> Entry | None:
        """What a state pill would have said (``docs/adr/0148`` §6).

        ``None`` in a room where nothing has happened yet, which is a real state:
        the opening is not a line, so a room whose game was just booked has no
        entry at all and still has to draw a row.
        """

        return self.entries[-1] if self.entries else None

    def pull_events(self) -> list[DomainEvent]:
        return self._events.pull()

    # -- opening ----------------------------------------------------------

    @classmethod
    def opened(
        cls,
        *,
        conversation_id: UUID,
        booking_id: UUID,
        sport: Sport,
        occurred_at: Instant,
    ) -> "Conversation":
        """Open the room. **The opening is the news, and it writes no line.**

        ``seq`` 1 is whatever happens next. The people booked on the game are
        its members from the start, visible in membership rather than announced
        in a backlog nobody could have been reading.
        """

        room = cls._empty()
        room._record_that(
            ConversationOpened(
                conversation_id=conversation_id,
                booking_id=booking_id,
                sport=sport.value,
                occurred_at=occurred_at,
            )
        )
        return room

    # -- being told -------------------------------------------------------

    def note_game(
        self,
        *,
        game_id: UUID,
        occurred_at: Instant,
        starts_at: Instant | None = None,
    ) -> None:
        """The game this room is about. **Told, and drawn rather than announced.**

        ``occurred_at`` is the moment the game was booked, and it is kept: it is
        ``Game.planned_at``, which is what this room's own end is anchored on
        (``docs/adr/0153`` §2), beside the hour it is played.

        Told a second time, this records nothing: the outbox is at-least-once and
        one booking is one game, so a second telling can only be a redelivery.
        """

        if self.game_id is not None:
            return
        self._record_that(
            GameNoted(
                conversation_id=self.conversation_id,
                game_id=game_id,
                occurred_at=occurred_at,
                starts_at=starts_at,
            )
        )

    def record_line(
        self,
        *,
        code: SystemLineCode,
        actor_id: UUID | None,
        values: Mapping[str, str],
        source_event_id: UUID,
        occurred_at: Instant,
    ) -> SystemLine:
        """Write what happened elsewhere into the stream, as a code and its values.

        **A redelivery answers the line that already stands and records
        nothing.** ``source_event_id`` is the outbox row that caused it, so this
        recognises the same telling arriving twice without needing a second
        identity for the line.
        """

        already = self._line_told_by(source_event_id)
        if already is not None:
            return already

        line = SystemLine(
            seq=self.last_seq + 1,
            code=code,
            actor_id=actor_id,
            values=dict(values),
            occurred_at=occurred_at,
        )
        self._record_that(
            SystemLineRecorded(
                conversation_id=self.conversation_id,
                seq=line.seq,
                code=code.value,
                actor_id=actor_id,
                values=dict(values),
                source_event_id=source_event_id,
                occurred_at=occurred_at,
            )
        )
        return line

    # -- saying something -------------------------------------------------

    def say(
        self,
        *,
        author_id: UUID,
        client_message_id: UUID,
        text: str,
        occurred_at: Instant,
    ) -> Message:
        """Put a player's own words in the stream.

        **A repeat answers the same message and the same ``seq``, recording
        nothing** (``docs/adr/0148`` §5). The client's id does two jobs — the
        idempotency key and the key an optimistic bubble is reconciled on — and
        one mechanism for one fact is what this repository refuses to have two
        of.

        **The refusals belong to ``MessageText``**, not to this method: a
        message arrives from a person typing it, so the value object trims the
        ends and then refuses an empty or an over-long one with its own code
        rather than being fixed into something nobody sent.
        """

        already = self._message_sent_by(author_id, client_message_id)
        if already is not None:
            return already

        said = MessageText.of(text)
        message = Message(
            seq=self.last_seq + 1,
            author_id=author_id,
            client_message_id=client_message_id,
            text=said,
            sent_at=occurred_at,
        )
        self._record_that(
            MessageSent(
                conversation_id=self.conversation_id,
                seq=message.seq,
                author_id=author_id,
                client_message_id=client_message_id,
                text=said.value,
                occurred_at=occurred_at,
            )
        )
        return message

    # -- reading ----------------------------------------------------------

    def page_back(self, *, before_seq: int | None, limit: int) -> tuple[Entry, ...]:
        """One page, ending just before ``before_seq``. **Oldest first inside it.**

        ``before_seq`` is **exclusive**, and ``None`` asks for the newest page.
        There is no ``has_more`` to answer with and none is wanted: the sequence
        is gapless, so ``seq`` 1 *is* the beginning of the conversation and a
        flag beside that would be the same fact twice
        (``docs/adr/0148`` §3).
        """

        invariant(limit >= 1, f"a page of {limit} entries")
        older = (
            self.entries
            if before_seq is None
            else tuple(entry for entry in self.entries if entry.seq < before_seq)
        )
        return older[-limit:]

    # -- folding ----------------------------------------------------------

    @classmethod
    def from_history(cls, events: Iterable[DomainEvent]) -> "Conversation":
        """Rebuild from the stream. **The opening event is the constructor.**"""

        room = cls._empty()
        for event in events:
            room._apply(event)
        return room

    @classmethod
    def _empty(cls) -> "Conversation":
        room = cls.__new__(cls)
        room.version = 0
        room.game_id = None
        room.planned_at = None
        room.starts_at = None
        room.entries = ()
        room._told_by = {}
        room._events = EventRecorder()
        return room

    def _record_that(self, event: DomainEvent) -> None:
        self._apply(event)
        self._events.record(event)

    def _apply(self, event: DomainEvent) -> None:
        """Fold one event. **Two of them are entries**; the others are not."""

        if isinstance(event, ConversationOpened):
            self.conversation_id = event.conversation_id
            self.booking_id = event.booking_id
            self.sport = Sport(event.sport)
            self.opened_at = instant(event.occurred_at)
        elif isinstance(event, ConversationOpenedUnderAChallengeId):
            # The first version, as stored: the id it carries is the booking's
            # on every room a booked game opened (``domain/events.py``).
            self.conversation_id = event.conversation_id
            self.booking_id = event.challenge_id
            self.sport = Sport(event.sport)
            self.opened_at = instant(event.occurred_at)
        elif isinstance(event, GameNoted):
            self.game_id = event.game_id
            self.planned_at = instant(event.occurred_at)
            self.starts_at = (
                None if event.starts_at is None else instant(event.starts_at)
            )
        elif isinstance(event, MessageSent):
            self.entries += (
                Message(
                    seq=event.seq,
                    author_id=event.author_id,
                    client_message_id=event.client_message_id,
                    # Folded through the value object, so a stored message meets
                    # the same rules a new one does — and a row that could not
                    # is a row this aggregate should refuse to replay silently.
                    text=MessageText.of(event.text),
                    sent_at=instant(event.occurred_at),
                ),
            )
        elif isinstance(event, SystemLineRecorded):
            self._told_by[event.source_event_id] = event.seq
            self.entries += (
                SystemLine(
                    seq=event.seq,
                    code=SystemLineCode(event.code),
                    actor_id=event.actor_id,
                    values=dict(event.values),
                    occurred_at=instant(event.occurred_at),
                ),
            )
        self.version += 1

    # -- the two idempotency reads ----------------------------------------

    def _line_told_by(self, source_event_id: UUID) -> SystemLine | None:
        seq = self._told_by.get(source_event_id)
        if seq is None:
            return None
        # The sequence is gapless and starts at one, so an entry's ``seq`` is
        # its position. That is the one place in this module the promise is
        # *used* rather than merely made, which is why it is checked here.
        found = self.entries[seq - 1]
        invariant(
            isinstance(found, SystemLine) and found.seq == seq,
            f"the stream is not gapless: seq {seq} is {found!r}",
        )
        return found  # type: ignore[return-value]

    def _message_sent_by(
        self, author_id: UUID, client_message_id: UUID
    ) -> Message | None:
        """*Has this person already sent this?*

        **The author is half the key**, because the id is the *client's* and two
        clients are two id spaces: matching on the value alone would let one
        member's send answer with another member's message. The collision is
        vanishingly unlikely and the fix costs a comparison, which is the whole
        argument for making it here rather than trusting a uuid.
        """

        for entry in reversed(self.entries):
            if (
                isinstance(entry, Message)
                and entry.client_message_id == client_message_id
                and entry.author_id == author_id
            ):
                return entry
        return None
