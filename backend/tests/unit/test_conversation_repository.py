"""The conversation row: the allocator, the lock, and *one arrangement is one room*.

The aggregate's own suite proves the sequence is gapless in memory. What is here
is the half that lives in the database: that the row mirrors the aggregate's
``last_seq``, that the lookup that opens a room is the one that takes the lock,
and that a second room for one challenge is refused by the schema rather than by
somebody remembering to check.

**The lock itself is not asserted, and that is stated rather than hidden.**
SQLAlchemy's SQLite dialect renders no ``FOR UPDATE``, and this suite runs one
connection over one in-memory database — so the path that needs the lock is
exercised against Postgres or not at all, the same honest split
``CandidateIndexTail`` states about its own snapshot horizon.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.bootstrap.composition import (
    build_conversation_repository,
    build_domain_event_store,
    build_event_publisher,
)
from app.kernel import Sport, instant
from app.modules.conversations.domain.conversation import Conversation
from app.modules.conversations.domain.entries import SystemLineCode
from app.modules.conversations.infrastructure.conversation_model import (
    ConversationORM,
)

NOW = instant(datetime(2026, 9, 8, 18, 0, tzinfo=timezone.utc))


def _later(minutes: int):
    return instant(NOW + timedelta(minutes=minutes))


@pytest_asyncio.fixture
async def session(session_factory):
    async with session_factory() as open_session:
        yield open_session


@pytest.fixture
def conversations(session):
    return build_conversation_repository(
        session=session,
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    )


def _opened(challenge_id) -> Conversation:
    return Conversation.opened(
        conversation_id=uuid4(),
        challenge_id=challenge_id,
        sport=Sport.PADEL,
        occurred_at=NOW,
    )


async def _row(session, conversation_id) -> ConversationORM:
    found = await session.execute(
        select(ConversationORM).where(
            ConversationORM.conversation_id == conversation_id
        )
    )
    return found.scalars().one()


async def test_an_opened_room_writes_a_row_whose_count_is_nought(
    conversations, session
):
    """``seq`` 1 is whatever happens next, so a fresh room has landed nothing."""

    room = _opened(uuid4())
    await conversations.save(room)
    await session.commit()

    row = await _row(session, room.conversation_id)

    assert row.last_seq == 0
    assert row.game_id is None
    assert row.sport == "PADEL"


async def test_the_row_mirrors_the_aggregates_count_on_every_append(
    conversations, session
):
    """Two copies of one number, and the reason is ``docs/adr/0147`` §2: the
    column is the **allocator's** — what the lock is taken on and what the live
    channel publishes — while the aggregate folds its own from its entries. This
    is what keeps them equal."""

    room = _opened(uuid4())
    await conversations.save(room)
    await session.commit()

    for n in range(1, 4):
        loaded = await conversations.load_for_append(room.conversation_id)
        loaded.say(
            author_id=uuid4(),
            client_message_id=uuid4(),
            text=f"{n}",
            occurred_at=_later(n),
        )
        await conversations.save(loaded)
        await session.commit()
        assert (await _row(session, room.conversation_id)).last_seq == loaded.last_seq

    assert (await _row(session, room.conversation_id)).last_seq == 3


async def test_appends_through_the_locking_read_leave_no_gap_and_no_duplicate(
    conversations, session
):
    """The sequence a reader pages over, built the way the platform builds one:
    every append reloads through ``load_for_append``, which is the read that
    takes the row's lock."""

    room = _opened(uuid4())
    await conversations.save(room)
    await session.commit()

    for n in range(1, 6):
        loaded = await conversations.load_for_append(room.conversation_id)
        if n % 2:
            loaded.say(
                author_id=uuid4(),
                client_message_id=uuid4(),
                text=f"{n}",
                occurred_at=_later(n),
            )
        else:
            loaded.record_line(
                code=SystemLineCode.SEAT_ACCEPTED,
                actor_id=uuid4(),
                values={},
                source_event_id=uuid4(),
                occurred_at=_later(n),
            )
        await conversations.save(loaded)
        await session.commit()

    folded = await conversations.load(room.conversation_id)

    assert [entry.seq for entry in folded.entries] == [1, 2, 3, 4, 5]


async def test_the_room_a_challenge_opened_is_found_by_that_challenge(
    conversations, session
):
    challenge_id = uuid4()
    room = _opened(challenge_id)
    await conversations.save(room)
    await session.commit()

    found = await conversations.for_challenge(challenge_id)

    assert found is not None
    assert found.conversation_id == room.conversation_id
    assert await conversations.for_challenge(uuid4()) is None


async def test_one_arrangement_is_one_room_and_the_schema_says_so(
    conversations, session
):
    """The unique index is the invariant. Without it, two acceptances arriving in
    one outbox poll would open two rooms for one court."""

    challenge_id = uuid4()
    await conversations.save(_opened(challenge_id))
    await session.commit()

    await conversations.save(_opened(challenge_id))
    with pytest.raises(IntegrityError):
        await session.commit()


async def test_the_game_reaches_the_row_so_the_played_line_can_find_it(
    conversations, session
):
    """``GamePlayed`` names a game and nothing else, which is why ``GamePlanned``
    has to reach the room even though it draws nothing."""

    room = _opened(uuid4())
    await conversations.save(room)
    await session.commit()
    game_id = uuid4()

    loaded = await conversations.load_for_append(room.conversation_id)
    loaded.note_game(game_id=game_id, occurred_at=_later(1))
    await conversations.save(loaded)
    await session.commit()

    assert (await _row(session, room.conversation_id)).game_id == game_id


async def test_a_room_that_was_never_opened_loads_as_nothing(conversations):
    assert await conversations.load(uuid4()) is None
    assert await conversations.load_for_append(uuid4()) is None
