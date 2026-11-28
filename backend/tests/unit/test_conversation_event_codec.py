"""Every Conversation event survives the round trip through storage, and the
opening is read at both of its versions.

A durable name is a **published contract**, so two things are asserted: that each
event has one, and that an event decoded out of the store equals the event that
was appended — **including the nullable actor**. ``SystemLineRecorded.actor_id``
is ``UUID | None``, and a codec that coerces only a bare ``UUID`` hint hands a
replayed line its actor as a string: equal to no member's id, unsortable beside
one, and the reason a face read keyed on it could answer nothing
([#408](https://github.com/Rakieta02/Rakieta/issues/408)).

**The opening is written at version 2 and read at 1 and 2** (#575): version 1
named the room's arrangement ``challenge_id``, and a stored room opened under it
still folds, with that id as its ``booking_id``.
"""

from __future__ import annotations

import pytest

from app.application.events import EventCatalog
from app.application.events.envelope import SerializedEventEnvelope
from app.modules.conversations.application.event_subscriptions import (
    _CONTRACTS,
    register_conversation_events,
)
from app.modules.conversations.domain.conversation import Conversation
from app.modules.conversations.domain.entries import DEPARTURE, SystemLineCode
from app.modules.conversations.domain.events import (
    ConversationOpened,
    ConversationOpenedUnderAChallengeId,
    GameNoted,
    MessageSent,
    SystemLineRecorded,
)
from app.infrastructure.events.json_event_codec import JsonEventCodec
from app.shared.ids import new_uuid
from tests.unit.fake_event_store import utc

ROOM = new_uuid()
BOOKING = new_uuid()
GAME = new_uuid()
SOMEBODY = new_uuid()
AT = utc(2026, 9, 11)


def domain_event_codec() -> JsonEventCodec:
    catalog = EventCatalog()
    register_conversation_events(catalog)
    return JsonEventCodec(catalog)


def _round_trip(codec: JsonEventCodec, event):
    encoded = codec.encode(event)
    return codec.decode(
        SerializedEventEnvelope(
            id=new_uuid(),
            event_type=encoded.event_type,
            schema_version=encoded.schema_version,
            payload=encoded.payload,
            occurred_at=event.occurred_at,
        )
    )


EVENTS = [
    ConversationOpened(
        conversation_id=ROOM, booking_id=BOOKING, sport="PADEL", occurred_at=AT
    ),
    ConversationOpenedUnderAChallengeId(
        conversation_id=ROOM, challenge_id=BOOKING, sport="PADEL", occurred_at=AT
    ),
    GameNoted(conversation_id=ROOM, game_id=GAME, occurred_at=AT, starts_at=AT),
    GameNoted(conversation_id=ROOM, game_id=GAME, occurred_at=AT),
    MessageSent(
        conversation_id=ROOM,
        seq=1,
        author_id=SOMEBODY,
        client_message_id=new_uuid(),
        text="where do we meet?",
        occurred_at=AT,
    ),
    SystemLineRecorded(
        conversation_id=ROOM,
        seq=2,
        code=SystemLineCode.SEAT_LEFT.value,
        actor_id=SOMEBODY,
        values={DEPARTURE: "DECLINED"},
        source_event_id=new_uuid(),
        occurred_at=AT,
    ),
    SystemLineRecorded(
        conversation_id=ROOM,
        seq=3,
        code=SystemLineCode.GAME_PLAYED.value,
        actor_id=None,
        values={},
        source_event_id=new_uuid(),
        occurred_at=AT,
    ),
]


@pytest.mark.parametrize("event", EVENTS, ids=lambda event: type(event).__name__)
def test_an_event_decodes_back_into_the_event_that_was_appended(event):
    assert _round_trip(domain_event_codec(), event) == event


def test_a_replayed_line_names_its_actor_by_id_and_never_by_text():
    """The half of the round trip that equality alone would hide if the fixture
    happened to compare strings: the decoded actor is the same **type** the
    aggregate compares members against."""

    decoded = _round_trip(domain_event_codec(), EVENTS[5])

    assert decoded.actor_id == SOMEBODY
    assert type(decoded.actor_id) is type(SOMEBODY)


def test_the_opening_is_written_at_version_2_under_its_booking():
    encoded = domain_event_codec().encode(EVENTS[0])

    assert (encoded.event_type, encoded.schema_version) == ("conversations.opened", 2)
    assert encoded.payload["booking_id"] == str(BOOKING)
    assert "challenge_id" not in encoded.payload


def test_a_stored_version_1_opening_folds_its_challenge_id_as_the_booking():
    """A room opened before #575 is still a room: the sweep has to fold it to
    destroy it, and the id it was filed under is the booking's."""

    written_before_the_rename = {
        "conversation_id": str(ROOM),
        "challenge_id": str(BOOKING),
        "sport": "PADEL",
        "occurred_at": AT.isoformat(),
    }

    opened = domain_event_codec().decode(
        SerializedEventEnvelope(
            id=new_uuid(),
            event_type="conversations.opened",
            schema_version=1,
            payload=written_before_the_rename,
            occurred_at=AT,
        )
    )
    room = Conversation.from_history([opened])

    assert isinstance(opened, ConversationOpenedUnderAChallengeId)
    assert opened.challenge_id == BOOKING
    assert (room.conversation_id, room.booking_id) == (ROOM, BOOKING)


def test_every_event_has_a_durable_name_and_no_name_says_the_room_has_ended():
    catalog = EventCatalog()
    register_conversation_events(catalog)

    names = {name for _, name, _ in _CONTRACTS}

    assert names == {
        "conversations.opened",
        "conversations.game_noted",
        "conversations.message_sent",
        "conversations.system_line_recorded",
    }
    for event_cls, name, version in _CONTRACTS:
        contract = catalog.contract_for(event_cls)
        assert (contract.name, contract.version) == (name, version)
    assert not any(word in name for name in names for word in ("closed", "ended"))
