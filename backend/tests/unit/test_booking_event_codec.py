"""What #669 takes off the Booking stream, as a **durable** contract: On
request's seven events leave **without decoders** — the local store is reset
with the removal and only ``local`` has ever run — while every event of a game
born booked still encodes and decodes under its own name.

**And what #671 adds to it**: the booked court's kind, indoor or outdoor, on
``bookings.confirmed`` and ``bookings.court_moved`` — each at **version 2**,
since a required fact joined the wire shape, and version 1 of each left
without a decoder, the store reset once more (Q122).
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.application.events import EventCatalog
from app.application.events.envelope import SerializedEventEnvelope
from app.infrastructure.events.json_event_codec import JsonEventCodec
from app.modules.bookings.application.event_subscriptions import (
    register_booking_events,
)
from app.modules.bookings.domain.events import (
    BookedByAFriend,
    BookingConfirmed,
    CalledOffBySender,
    CourtMoved,
    CoverWarned,
    InvitedSeatAccepted,
    InvitedSeatDeclined,
    InvitedSeatRanOut,
    InvitedSeatTaken,
    SeatInvited,
    SeatOpened,
)

NOW = datetime(2026, 10, 5, 6, tzinfo=timezone.utc)
START = datetime(2026, 10, 10, 15, tzinfo=timezone.utc)

#: On request's events, unregistered with it (#669).
REMOVED = (
    "bookings.requested",
    "bookings.accepted",
    "bookings.refused",
    "bookings.timed_out",
    "bookings.request_withdrawn",
    "bookings.awaiting_a_payment",
    "bookings.payment_not_in_time",
)


def _catalog() -> EventCatalog:
    catalog = EventCatalog()
    register_booking_events(catalog)
    return catalog


def _confirmed() -> BookingConfirmed:
    return BookingConfirmed(
        booking_id=uuid4(),
        pool_id=uuid4(),
        club_id=uuid4(),
        court_id=uuid4(),
        court_name="Court 1",
        indoor=True,
        sport="PADEL",
        kind="COMPETITIVE",
        start=START,
        share_grosze=30_00,
        first_side=(uuid4(), uuid4()),
        second_side=(uuid4(), uuid4()),
        cut_off=START,
        game_id=uuid4(),
        occurred_at=NOW,
    )


def test_a_booking_born_booked_encodes_and_decodes_back():
    codec = JsonEventCodec(_catalog())
    confirmed = _confirmed()

    encoded = codec.encode(confirmed)

    assert (encoded.event_type, encoded.schema_version) == ("bookings.confirmed", 2)
    decoded = codec.decode(
        SerializedEventEnvelope(
            id=uuid4(),
            event_type=encoded.event_type,
            schema_version=encoded.schema_version,
            payload=encoded.payload,
            occurred_at=NOW,
        )
    )
    assert decoded == confirmed


def test_a_move_carries_the_new_court_s_kind_at_version_2():
    codec = JsonEventCodec(_catalog())
    moved = CourtMoved(
        booking_id=uuid4(),
        court_id=uuid4(),
        court_name="Court 4",
        indoor=False,
        occurred_at=NOW,
    )

    encoded = codec.encode(moved)

    assert (encoded.event_type, encoded.schema_version) == ("bookings.court_moved", 2)
    decoded = codec.decode(
        SerializedEventEnvelope(
            id=uuid4(),
            event_type=encoded.event_type,
            schema_version=encoded.schema_version,
            payload=encoded.payload,
            occurred_at=NOW,
        )
    )
    assert decoded == moved


@pytest.mark.parametrize("name", REMOVED)
def test_on_request_s_events_have_no_decoder(name: str):
    with pytest.raises(LookupError):
        _catalog().class_for(name, 1)


@pytest.mark.parametrize("name", ["bookings.confirmed", "bookings.court_moved"])
def test_a_booking_or_a_move_without_the_court_s_kind_has_no_decoder(name: str):
    """Version 1 named the court and never its kind (#671): a row of it is a
    decoding error, the store reset with the change."""

    with pytest.raises(LookupError):
        _catalog().class_for(name, 1)


def test_a_move_by_cancel_keeps_its_reason_and_the_court_it_left():
    """#672: a club's cancel that a free court absorbed is a ``CourtMoved``
    naming the cancel's reason and the court the game left — two defaulted
    fields, version 2 unchanged."""

    codec = JsonEventCodec(_catalog())
    moved = CourtMoved(
        booking_id=uuid4(),
        court_id=uuid4(),
        court_name="Court 3",
        indoor=True,
        occurred_at=NOW,
        reason="REPAIR",
        moved_from="Court 2",
    )

    encoded = codec.encode(moved)

    assert encoded.schema_version == 2
    assert codec.decode(_envelope(encoded)) == moved


def test_a_move_recorded_before_reads_as_the_club_s_own():
    codec = JsonEventCodec(_catalog())
    encoded = codec.encode(
        CourtMoved(
            booking_id=uuid4(),
            court_id=uuid4(),
            court_name="Court 3",
            indoor=True,
            occurred_at=NOW,
        )
    )
    before = {
        key: value
        for key, value in encoded.payload.items()
        if key not in ("reason", "moved_from")
    }

    decoded = codec.decode(_envelope(encoded, payload=before))

    assert isinstance(decoded, CourtMoved)
    assert (decoded.reason, decoded.moved_from) == (None, None)


def _envelope(encoded, *, payload=None) -> SerializedEventEnvelope:
    return SerializedEventEnvelope(
        id=uuid4(),
        event_type=encoded.event_type,
        schema_version=encoded.schema_version,
        payload=encoded.payload if payload is None else payload,
        occurred_at=NOW,
    )


def _friends_game_events() -> list[object]:
    booking = uuid4()
    return [
        BookedByAFriend(
            booking_id=booking,
            pool_id=uuid4(),
            club_id=uuid4(),
            court_id=uuid4(),
            court_name="Court 3",
            indoor=True,
            sport="PADEL",
            kind="COMPETITIVE",
            start=START,
            share_grosze=25_00,
            sender_id=uuid4(),
            first_side=(uuid4(), uuid4()),
            second_side=(uuid4(), uuid4()),
            pay_mode="SPLIT_THE_COST",
            invited_until=START,
            cut_off=START,
            game_id=uuid4(),
            occurred_at=NOW,
        ),
        InvitedSeatAccepted(
            booking_id=booking, player_id=uuid4(), side="B", occurred_at=NOW
        ),
        InvitedSeatDeclined(booking_id=booking, player_id=uuid4(), occurred_at=NOW),
        InvitedSeatRanOut(booking_id=booking, player_id=uuid4(), occurred_at=NOW),
        CalledOffBySender(
            booking_id=booking,
            player_ids=(uuid4(),),
            invited=(uuid4(), uuid4()),
            occurred_at=NOW,
        ),
        SeatInvited(
            booking_id=booking,
            player_id=uuid4(),
            invited_by=uuid4(),
            seat_of=uuid4(),
            side="B",
            until=START,
            occurred_at=NOW,
        ),
        InvitedSeatTaken(
            booking_id=booking, player_id=uuid4(), taken_by=uuid4(), occurred_at=NOW
        ),
        SeatOpened(
            booking_id=booking, seat_of=uuid4(), occurred_at=NOW, at_the_cut_off=True
        ),
        CoverWarned(
            booking_id=booking, sender_id=uuid4(), seats=(uuid4(),), occurred_at=NOW
        ),
    ]


@pytest.mark.parametrize(
    ("event", "name"),
    zip(
        _friends_game_events(),
        (
            "bookings.booked_by_a_friend",
            "bookings.invited_seat_accepted",
            "bookings.invited_seat_declined",
            "bookings.invited_seat_ran_out",
            "bookings.called_off_by_the_sender",
            "bookings.seat_invited",
            "bookings.invited_seat_taken",
            "bookings.seat_opened",
            "bookings.cover_warned",
        ),
        strict=True,
    ),
)
def test_a_friends_game_s_events_encode_and_decode_at_version_1(event, name):
    """#751: the Booking's second birth and its invited seats' answers — and
    #752's empty seats: invited into, taken first, opened, and warned of."""

    codec = JsonEventCodec(_catalog())

    encoded = codec.encode(event)

    assert (encoded.event_type, encoded.schema_version) == (name, 1)
    assert codec.decode(_envelope(encoded)) == event
