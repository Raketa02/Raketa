"""What #622 adds to the Booking stream, as a **durable** contract: a request
names the player whose own act put it to the club — defaulted rather than a
version 2, so a request stored before names nobody, and nobody's *It's a
game!* about it is their own.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.application.events import EventCatalog
from app.application.events.envelope import SerializedEventEnvelope
from app.infrastructure.events.json_event_codec import JsonEventCodec
from app.modules.bookings.application.event_subscriptions import (
    register_booking_events,
)
from app.modules.bookings.domain.events import BookingRequested

NOW = datetime(2026, 10, 5, 6, tzinfo=timezone.utc)
START = datetime(2026, 10, 10, 15, tzinfo=timezone.utc)
FILLER = uuid4()


def _codec() -> JsonEventCodec:
    catalog = EventCatalog()
    register_booking_events(catalog)
    return JsonEventCodec(catalog)


def _requested() -> BookingRequested:
    return BookingRequested(
        booking_id=uuid4(),
        pool_id=uuid4(),
        club_id=uuid4(),
        court_id=uuid4(),
        court_name="Court 1",
        sport="PADEL",
        kind="COMPETITIVE",
        start=START,
        share_grosze=30_00,
        first_side=(FILLER, uuid4()),
        second_side=(uuid4(), uuid4()),
        cut_off=START,
        answer_by=datetime(2026, 10, 5, 6, 30, tzinfo=timezone.utc),
        occurred_at=NOW,
        filled_by=FILLER,
    )


def _decoded(codec: JsonEventCodec, event_type: str, payload: dict):
    return codec.decode(
        SerializedEventEnvelope(
            id=uuid4(),
            event_type=event_type,
            schema_version=1,
            payload=payload,
            occurred_at=NOW,
        )
    )


def test_a_request_names_whose_act_put_it_to_the_club_and_decodes_back():
    codec = _codec()
    requested = _requested()

    encoded = codec.encode(requested)

    assert (encoded.event_type, encoded.schema_version) == ("bookings.requested", 1)
    assert _decoded(codec, encoded.event_type, encoded.payload) == requested


def test_a_request_stored_before_it_named_its_filler_names_nobody():
    codec = _codec()
    encoded = codec.encode(_requested())
    older = {key: value for key, value in encoded.payload.items() if key != "filled_by"}

    decoded = _decoded(codec, encoded.event_type, older)

    assert isinstance(decoded, BookingRequested)
    assert decoded.filled_by is None
