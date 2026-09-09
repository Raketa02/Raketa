"""The Conversation aggregate: the sequence, the two shapes, and what opens a room.

Every test here names the record it is defending. What is asserted is the
aggregate and its events — never a repository call count.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.kernel import Sport, instant
from app.modules.conversations.domain.conversation import Conversation
from app.modules.conversations.domain.entries import (
    COUNT,
    DEPARTURE,
    MESSAGE_LENGTH_CAP,
    Message,
    SeatDeparture,
    SystemLine,
    SystemLineCode,
)
from app.modules.conversations.domain.errors import (
    AMessageMustSaySomething,
    TheMessageIsTooLong,
)
from app.modules.conversations.domain.events import (
    ConversationOpened,
    GameNoted,
    MessageSent,
    SystemLineRecorded,
)

NOW = instant(datetime(2026, 9, 8, 18, 0, tzinfo=timezone.utc))


def _later(minutes: int):
    return instant(NOW + timedelta(minutes=minutes))


def _opened() -> Conversation:
    return Conversation.opened(
        conversation_id=uuid4(),
        challenge_id=uuid4(),
        sport=Sport.PADEL,
        occurred_at=NOW,
    )


def _replayed(room: Conversation) -> Conversation:
    """The same room, folded back from its own stream."""

    return Conversation.from_history(room.pull_events())


# -- opening ---------------------------------------------------------------


def test_a_room_opens_with_no_entries_because_the_opening_is_not_a_line():
    """``the-words.md`` §23.1 — *it is the opening; ``seq`` 1 is whatever
    happens next.*"""

    room = _opened()

    assert room.entries == ()
    assert room.last_seq == 0
    assert [type(event) for event in room.pull_events()] == [ConversationOpened]


def test_the_opening_stores_no_members_because_membership_is_derived():
    """``docs/adr/0146`` §7 — never stored, from whichever record is arranging."""

    room = _opened()

    opened = room.pull_events()[0]
    assert not any("member" in field for field in vars(opened))


# -- the sequence ----------------------------------------------------------


def test_the_sequence_starts_at_one_and_is_gapless_across_both_shapes():
    """``docs/adr/0147`` §2 — one ordered stream, one sequence number."""

    room = _opened()
    author = uuid4()

    room.say(
        author_id=author,
        client_message_id=uuid4(),
        text="six?",
        occurred_at=_later(1),
    )
    room.record_line(
        code=SystemLineCode.SEAT_ACCEPTED,
        actor_id=uuid4(),
        values={},
        source_event_id=uuid4(),
        occurred_at=_later(2),
    )
    room.say(
        author_id=author,
        client_message_id=uuid4(),
        text="or seven",
        occurred_at=_later(3),
    )

    assert [entry.seq for entry in room.entries] == [1, 2, 3]
    assert room.last_seq == 3


def test_the_sequence_survives_a_replay_of_the_stream():
    room = _opened()
    room.say(
        author_id=uuid4(),
        client_message_id=uuid4(),
        text="hello",
        occurred_at=_later(1),
    )

    replayed = _replayed(room)

    assert [entry.seq for entry in replayed.entries] == [1]
    assert replayed.last_seq == 1


# -- messages --------------------------------------------------------------


def test_a_message_carries_no_id_of_its_own():
    """``docs/adr/0148`` §4 — ``(conversation_id, seq)`` already identifies it."""

    assert not hasattr(Message(
        seq=1,
        author_id=uuid4(),
        client_message_id=uuid4(),
        text="hi",
        sent_at=NOW,
    ), "id")


def test_the_same_client_message_id_records_nothing_and_answers_the_same_seq():
    """``docs/adr/0148`` §5 — a resumed send must not become two messages."""

    room = _opened()
    client_id = uuid4()
    author = uuid4()

    first = room.say(
        author_id=author,
        client_message_id=client_id,
        text="on my way",
        occurred_at=_later(1),
    )
    room.pull_events()
    again = room.say(
        author_id=author,
        client_message_id=client_id,
        text="on my way",
        occurred_at=_later(9),
    )

    assert again == first
    assert again.seq == 1
    assert room.pull_events() == []
    assert len(room.entries) == 1


def test_an_empty_message_is_refused_rather_than_recorded():
    room = _opened()

    with pytest.raises(AMessageMustSaySomething):
        room.say(
            author_id=uuid4(),
            client_message_id=uuid4(),
            text="   ",
            occurred_at=_later(1),
        )


def test_a_message_past_the_cap_is_refused_rather_than_truncated():
    room = _opened()

    with pytest.raises(TheMessageIsTooLong):
        room.say(
            author_id=uuid4(),
            client_message_id=uuid4(),
            text="x" * (MESSAGE_LENGTH_CAP + 1),
            occurred_at=_later(1),
        )


# -- system lines ----------------------------------------------------------


def test_a_seat_leaving_is_one_code_with_the_answer_as_a_value():
    """``the-words.md`` §23 — a lapse is still not a decline, in the value."""

    room = _opened()
    declined = room.record_line(
        code=SystemLineCode.SEAT_LEFT,
        actor_id=uuid4(),
        values={DEPARTURE: SeatDeparture.DECLINED.value},
        source_event_id=uuid4(),
        occurred_at=_later(1),
    )
    lapsed = room.record_line(
        code=SystemLineCode.SEAT_LEFT,
        actor_id=uuid4(),
        values={DEPARTURE: SeatDeparture.LAPSED.value},
        source_event_id=uuid4(),
        occurred_at=_later(2),
    )

    assert declined.code is lapsed.code is SystemLineCode.SEAT_LEFT
    assert declined.values[DEPARTURE] != lapsed.values[DEPARTURE]


def test_a_redelivered_event_records_nothing():
    """The outbox is at-least-once, so a subscriber that writes is idempotent."""

    room = _opened()
    caused_by = uuid4()
    actor = uuid4()

    first = room.record_line(
        code=SystemLineCode.SEAT_ACCEPTED,
        actor_id=actor,
        values={},
        source_event_id=caused_by,
        occurred_at=_later(1),
    )
    room.pull_events()
    again = room.record_line(
        code=SystemLineCode.SEAT_ACCEPTED,
        actor_id=actor,
        values={},
        source_event_id=caused_by,
        occurred_at=_later(5),
    )

    assert again == first
    assert room.pull_events() == []
    assert len(room.entries) == 1


def test_values_carry_the_count_and_never_the_names():
    """``docs/adr/0148`` §4 — ``values`` never repeats what membership says."""

    room = _opened()

    line = room.record_line(
        code=SystemLineCode.SEATS_INVITED,
        actor_id=uuid4(),
        values={COUNT: "2"},
        source_event_id=uuid4(),
        occurred_at=_later(1),
    )

    assert set(line.values) == {COUNT}


# -- the game --------------------------------------------------------------


def test_noting_the_game_writes_no_line_and_is_told_once():
    """``the-words.md`` §23.1 — the seats already imply it, and the event still
    arrives because the room's own end is derived from its moment."""

    room = _opened()
    room.pull_events()
    game_id = uuid4()

    room.note_game(game_id=game_id, occurred_at=_later(1))
    events = room.pull_events()
    room.note_game(game_id=game_id, occurred_at=_later(2))

    assert room.game_id == game_id
    assert room.entries == ()
    assert [type(event) for event in events] == [GameNoted]
    assert room.pull_events() == []


def test_a_room_with_no_game_has_no_planned_at_and_one_with_a_game_keeps_it():
    """``docs/adr/0153`` §2 — ``Game.planned_at`` **is**
    ``GamePlanned.occurred_at``, and the telling that draws no line is where the
    room's own end gets its anchor. It costs no new event and no new field on the
    wire: the moment was already on the telling."""

    room = _opened()
    assert room.planned_at is None

    room.note_game(game_id=uuid4(), occurred_at=_later(1))

    assert room.planned_at == _later(1)
    assert _replayed(room).planned_at == _later(1)


def test_a_second_telling_of_the_game_does_not_move_the_anchor():
    """The outbox is at-least-once, and a redelivery must not re-date a room's
    end — which is the one thing that could make it move **later**."""

    room = _opened()
    room.note_game(game_id=uuid4(), occurred_at=_later(1))

    room.note_game(game_id=uuid4(), occurred_at=_later(500))

    assert room.planned_at == _later(1)


# -- paging ----------------------------------------------------------------


def test_the_newest_page_comes_back_oldest_first_within_the_page():
    room = _opened()
    for n in range(1, 8):
        room.say(
            author_id=uuid4(),
            client_message_id=uuid4(),
            text=f"{n}",
            occurred_at=_later(n),
        )

    page = room.page_back(before_seq=None, limit=3)

    assert [entry.seq for entry in page] == [5, 6, 7]


def test_paging_back_from_a_cursor_is_exclusive_and_reaches_seq_one():
    room = _opened()
    for n in range(1, 6):
        room.say(
            author_id=uuid4(),
            client_message_id=uuid4(),
            text=f"{n}",
            occurred_at=_later(n),
        )

    assert [e.seq for e in room.page_back(before_seq=4, limit=2)] == [2, 3]
    assert [e.seq for e in room.page_back(before_seq=2, limit=50)] == [1]
    assert room.page_back(before_seq=1, limit=50) == ()


def test_the_last_entry_is_absent_in_a_room_where_nothing_has_happened_yet():
    """``the-loop-screens.md`` §3.4 — the opening is not a line, so a freshly
    opened room genuinely has none, and the row still has to draw."""

    assert _opened().last_entry is None


def test_the_stream_folds_both_shapes_back_in_sequence_order():
    room = _opened()
    room.record_line(
        code=SystemLineCode.SEAT_ACCEPTED,
        actor_id=uuid4(),
        values={},
        source_event_id=uuid4(),
        occurred_at=_later(1),
    )
    room.say(
        author_id=uuid4(),
        client_message_id=uuid4(),
        text="hi",
        occurred_at=_later(2),
    )

    replayed = _replayed(room)

    assert [type(entry) for entry in replayed.entries] == [SystemLine, Message]
    assert isinstance(replayed.last_entry, Message)


def test_every_entry_event_carries_its_own_seq_and_never_the_stream_version():
    """``docs/adr/0147`` §2 — the opening holds a version and no ``seq``."""

    room = _opened()
    room.say(
        author_id=uuid4(),
        client_message_id=uuid4(),
        text="hi",
        occurred_at=_later(1),
    )

    opened, sent = room.pull_events()

    assert not hasattr(opened, "seq")
    assert isinstance(sent, MessageSent)
    assert sent.seq == 1


def test_a_line_and_a_message_never_share_a_seq():
    room = _opened()
    room.record_line(
        code=SystemLineCode.GAME_PLAYED,
        actor_id=uuid4(),
        values={},
        source_event_id=uuid4(),
        occurred_at=_later(1),
    )
    room.say(
        author_id=uuid4(),
        client_message_id=uuid4(),
        text="hi",
        occurred_at=_later(2),
    )

    entries = (MessageSent, SystemLineRecorded)
    events = [e for e in room.pull_events() if isinstance(e, entries)]

    assert [event.seq for event in events] == [1, 2]
