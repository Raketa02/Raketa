"""The Conversation repository, over the event store and one row.

The same fifteen lines the other aggregate repositories have — which aggregate
type the streams are filed under, that state is rebuilt by replaying them, and
what version the next append expects — plus the one thing no other context here
needs: **the sequence allocator's lock.**

**Two reads, and the difference is the whole of ``docs/adr/0147`` §2.** ``load``
serves a response. ``load_for_append`` and ``for_booking`` take the
conversation row ``FOR UPDATE`` first, so ``last_seq + 1`` is minted while
nobody else can be minting it. A single method with a flag would be one a caller
could forget, and the failure would be two people seeing one bubble twice under
load and nothing at all otherwise.

**The row is written from the aggregate and never read back into it.** The
aggregate folds ``last_seq`` from its own entries, which is the one place it is
true in the domain; the column is the allocator's copy and what the live channel
publishes without a second read. ``save`` keeps them equal, and a test asserts it
rather than trusting the two writes to stay in step.

**Nothing here commits.** The transaction boundary is the use case's — and for a
telling it is the outbox delivery's, so a system line and the row that said to
write it stand or fall together.

**On SQLite there is no lock and there is no concurrency either.** The dialect
renders no ``FOR UPDATE`` clause, and the test suite runs one connection over one
in-memory database, so the path that needs the lock is exercised against Postgres
or not at all — the same honest split ``CandidateIndexTail`` states about its own
horizon.
"""

from __future__ import annotations

from dataclasses import fields
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports import DomainEventPublisher, DomainEventStore
from app.infrastructure.events.event_store_model import EventStoreORM
from app.modules.conversations.domain.conversation import Conversation
from app.modules.conversations.domain.events import ConversationOpened
from app.modules.conversations.infrastructure.conversation_model import (
    ConversationORM,
)

CONVERSATION_AGGREGATE = "conversation"


def _opening_field(name: str) -> str:
    """A field on the opening event, checked at import.

    The row mirrors some of them, and what is avoidable about that coupling is
    it being *silent*: a renamed field would leave the row carrying a stale
    spelling for ever, and the failure would look like a room that had never been
    opened rather than like a bug.
    """

    if name not in {field.name for field in fields(ConversationOpened)}:
        raise RuntimeError(
            f"ConversationOpened has no field {name!r}: the conversation row "
            "mirrors it, and a rename would leave the two silently apart"
        )
    return name


BOOKING_ID = _opening_field("booking_id")


class EventSourcedConversationRepository:
    """``ConversationRepository`` over ``DomainEventStore`` and one locked row."""

    def __init__(
        self,
        *,
        event_store: DomainEventStore,
        events: DomainEventPublisher,
        session: AsyncSession,
    ) -> None:
        self._event_store = event_store
        self._events = events
        self._session = session
        # Aggregate id -> the stream version this request has seen. Read by
        # ``save`` as the expected version.
        self._versions: dict[UUID, int] = {}

    async def load(self, conversation_id: UUID) -> Conversation | None:
        return await self._folded(conversation_id)

    async def load_for_append(self, conversation_id: UUID) -> Conversation | None:
        if await self._locked_row(conversation_id) is None:
            return None
        return await self._folded(conversation_id)

    async def for_booking(self, booking_id: UUID) -> Conversation | None:
        """The room this booking's game already opened, **with its row locked**.

        Matched on the row rather than on the opening event's payload, because
        this read is the one that has to take the lock — and a lock is on a row.
        The unique index on ``booking_id`` is what makes it answer with one.
        """

        found = await self._session.execute(
            select(ConversationORM.conversation_id)
            .where(ConversationORM.booking_id == booking_id)
            .with_for_update()
        )
        conversation_id = found.scalars().first()
        if conversation_id is None:
            return None
        return await self._folded(conversation_id)

    async def save(self, conversation: Conversation) -> None:
        pending = conversation.pull_events()
        if not pending:
            return

        expected = self._versions.get(conversation.id, 0)
        await self._event_store.append(
            aggregate_type=CONVERSATION_AGGREGATE,
            aggregate_id=conversation.id,
            expected_version=expected,
            events=pending,
        )
        await self._events.publish_many(pending)

        if expected == 0:
            self._session.add(
                ConversationORM(
                    conversation_id=conversation.conversation_id,
                    booking_id=conversation.booking_id,
                    game_id=conversation.game_id,
                    sport=conversation.sport.value,
                    last_seq=conversation.last_seq,
                    opened_at=conversation.opened_at,
                )
            )
        else:
            row = await self._session.get(ConversationORM, conversation.conversation_id)
            if row is not None:
                row.game_id = conversation.game_id
                row.last_seq = conversation.last_seq
        # Deliberately no commit: the transaction boundary is the caller's.
        self._remember(conversation)

    async def destroy(self, conversation_id: UUID) -> None:
        """Delete the stream and the row. **Destroyed, not delisted.**

        Two statements and no aggregate, deliberately: there is no event to
        append and nothing to fold, because what this performs is the room
        ceasing to exist rather than something happening in it. A
        ``ConversationDestroyed`` on the stream it deletes would be a record of
        the destruction inside the thing destroyed.

        **The stream goes first.** A row with no stream is a room that folds to
        nothing and reads as absent; a stream with no row is one every locked
        read misses and nothing can ever sweep — so if only one of the two lands,
        it must be this one.

        **It leaves a hole in ``event_store.sequence_no``**, which the candidate
        index's tail is built for: a gap is stepped over once the snapshot
        horizon proves it permanent (``docs/adr/0110``), so a destruction costs
        that projection a tick of lag and never a lost event. The outbox rows
        these events were queued on carry their own payloads and are unaffected;
        nothing subscribes to a conversation's own events.

        **Idempotent**: deleting nothing is the state this asks for, and both
        callers — the call-off and the sweep — can run beside themselves.
        """

        await self._session.execute(
            delete(EventStoreORM).where(
                EventStoreORM.aggregate_type == CONVERSATION_AGGREGATE,
                EventStoreORM.aggregate_id == conversation_id,
            )
        )
        await self._session.execute(
            delete(ConversationORM).where(
                ConversationORM.conversation_id == conversation_id
            )
        )
        # Whatever version this request had seen is about to be a lie. Forgetting
        # it means a room re-opened under the same id in this same request — which
        # nothing does, and which is exactly why it must not silently half-work.
        self._versions.pop(conversation_id, None)
        # Deliberately no commit: the transaction boundary is the caller's.

    async def _folded(self, conversation_id: UUID) -> Conversation | None:
        stored = await self._event_store.load_stream(
            aggregate_type=CONVERSATION_AGGREGATE,
            aggregate_id=conversation_id,
        )
        if not stored:
            return None
        room = Conversation.from_history(record.event for record in stored)
        self._remember(room)
        return room

    async def _locked_row(self, conversation_id: UUID) -> UUID | None:
        found = await self._session.execute(
            select(ConversationORM.conversation_id)
            .where(ConversationORM.conversation_id == conversation_id)
            .with_for_update()
        )
        return found.scalars().first()

    def _remember(self, conversation: Conversation) -> None:
        self._versions[conversation.id] = conversation.version
