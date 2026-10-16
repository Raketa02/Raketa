"""Desk check-in is gone, and what it wrote still decodes and folds to nothing
(#651; ``docs/adr/0195`` §4, §9).

Check-ins lived only in event streams, so nothing was migrated: a booking's
stream may hold ``bookings.player_checked_in``. **Stored events outlive the
code that wrote them** (``.claude/rules/domain-events.md``), and every read of
a booking walks the whole stream — so the row still decodes, and the fold reads
it and changes nothing but the stream's version.

A club's Raketa settings rows carried ``check_in`` too, decodable until #670
moved ``clubs.raketa_settings_changed`` to version 2 with the store reset
(``test_club_event_codec.py``): a version 1 row is refused, and no version 2
row ever carried the switch.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone

from app.application.events import EventCatalog
from app.application.events.envelope import SerializedEventEnvelope
from app.engines.matchfit.core import SearchMode
from app.infrastructure.events.json_event_codec import JsonEventCodec
from app.kernel import Sport, instant
from app.modules.bookings.application.event_subscriptions import (
    register_booking_events,
)
from app.modules.bookings.domain.booking import BookedCourt, Booking
from app.shared.ids import new_uuid

OLA, KUBA, EWA, TOMEK = (new_uuid() for _ in range(4))
BOOKED_AT = instant(datetime(2026, 10, 5, 6, tzinfo=timezone.utc))
START = instant(BOOKED_AT + timedelta(days=5))


def _codec() -> JsonEventCodec:
    catalog = EventCatalog()
    register_booking_events(catalog)
    return JsonEventCodec(catalog)


def _row(event_type: str, payload: dict, *, at: datetime):
    return _codec().decode(
        SerializedEventEnvelope(
            id=new_uuid(),
            event_type=event_type,
            schema_version=1,
            payload=payload,
            occurred_at=instant(at),
        )
    )


def test_a_stored_check_in_decodes_and_folds_to_nothing_but_a_version():
    booking = Booking.confirmed(
        booking_id=new_uuid(),
        pool_id=new_uuid(),
        club_id=new_uuid(),
        court=BookedCourt(court_id=new_uuid(), name="Court 1", indoor=True),
        sport=Sport.PADEL,
        kind=SearchMode.COMPETITIVE,
        start=START,
        share_grosze=30_00,
        first_side=(OLA, KUBA),
        second_side=(EWA, TOMEK),
        cut_off=instant(START - timedelta(hours=24)),
        game_id=new_uuid(),
        at=BOOKED_AT,
    )
    [opening] = booking.pull_events()
    scanned_at = START - timedelta(minutes=8)
    checked_in = _row(
        "bookings.player_checked_in",
        {
            "booking_id": str(booking.booking_id),
            "player_id": str(EWA),
            "occurred_at": scanned_at.isoformat(),
        },
        at=scanned_at,
    )

    folded = Booking.from_history([opening, checked_in])

    assert folded == replace(Booking.from_history([opening]), version=2)
