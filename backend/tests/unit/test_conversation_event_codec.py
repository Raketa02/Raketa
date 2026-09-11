"""Every Conversation event survives the round trip through storage, and there
are four of them.

A durable name is a **published contract**, so two things are asserted: that each
event has one, and that an event decoded out of the store equals the event that
was appended — **including the nullable actor**. ``SystemLineRecorded.actor_id``
is ``UUID | None``, and a codec that coerces only a bare ``UUID`` hint hands a
replayed line its actor as a string: equal to no member's id, unsortable beside
one, and the reason a face read keyed on it could answer nothing
([#408](https://github.com/Raketa02/Raketa/issues/408)).
"""

from __future__ import annotations

import pytest

from app.application.events import EventCatalog
from app.application.events.envelope import SerializedEventEnvelope
from app.modules.conversations.application.event_subscriptions import (
    _CONTRACTS,
    register_conversation_events,
)
from app.modules.conversations.domain.entries import DEPARTURE, SystemLineCode
from app.modules.conversations.domain.events import (
    ConversationOpened,
    GameNoted,
    MessageSent,
    SystemLineRecorded,
)
from app.infrastructure.events.json_event_codec import JsonEventCodec
from app.shared.ids import new_uuid
from tests.unit.fake_event_store import utc

ROOM = new_uuid()
CHALLENGE = new_uuid()
GAME = new_uuid()
SOMEBODY = new_uuid()
AT = utc(2026, 9, 11)


def domain_event_codec() -> JsonEventCodec:
    catalog = EventCatalog()
    register_conversation_events(catalog)
    return JsonEventCodec(catalog)


EVENTS = [
    ConversationOpened(
        conversation_id=ROOM, challenge_id=CHALLENGE, sport="PADEL", occurred_at=AT
    ),
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
    codec = domain_event_codec()

    encoded = codec.encode(event)
    decoded = codec.decode(
        SerializedEventEnvelope(
            id=new_uuid(),
            event_type=encoded.event_type,
            schema_version=encoded.schema_version,
            payload=encoded.payload,
            occurred_at=event.occurred_at,
        )
    )

    assert decoded == event


def test_a_replayed_line_names_its_actor_by_id_and_never_by_text():
    """The half of the round trip that equality alone would hide if the fixture
    happened to compare strings: the decoded actor is the same **type** the
    aggregate compares members against."""

    codec = domain_event_codec()
    told = EVENTS[3]

    encoded = codec.encode(told)
    decoded = codec.decode(
        SerializedEventEnvelope(
            id=new_uuid(),
            event_type=encoded.event_type,
            schema_version=encoded.schema_version,
            payload=encoded.payload,
            occurred_at=told.occurred_at,
        )
    )

    assert decoded.actor_id == SOMEBODY
    assert type(decoded.actor_id) is type(SOMEBODY)


def test_every_event_has_a_durable_name_and_no_name_says_the_room_has_ended():
    catalog = EventCatalog()
    register_conversation_events(catalog)

    names = {name for _, name in _CONTRACTS}

    assert names == {
        "conversations.opened",
        "conversations.game_noted",
        "conversations.message_sent",
        "conversations.system_line_recorded",
    }
    for event_cls, name in _CONTRACTS:
        assert catalog.contract_for(event_cls).name == name
    assert not any(word in name for name in names for word in ("closed", "ended"))
