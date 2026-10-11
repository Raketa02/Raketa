"""The Club context's streams as a **durable** contract.

Asserted against the real catalog registration, because the name and version a
row is filed under are what history is recorded as. Two things could go wrong
invisibly and each has a case: a club's sports come back from JSON as a list,
so an event read back would be unequal to the one appended; and the account's
hash is on the account's stream and **never on the club's**, which is what the
search projection is built from (``docs/adr/0182`` §3).
"""

from __future__ import annotations

from dataclasses import fields
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.application.events import EventCatalog
from app.application.events.envelope import SerializedEventEnvelope
from app.infrastructure.events.json_event_codec import JsonEventCodec
from app.modules.clubs.application.event_subscriptions import register_club_events
from app.modules.clubs.domain.club_courts_events import (
    CourtAdded,
    CourtChanged,
    CourtRemoved,
    CourtSwitchedOff,
    CourtSwitchedOn,
    ExceptionAdded,
    ExceptionRemoved,
    PricesSet,
    RaketaHoursSet,
    RaketaPaused,
    RaketaResumed,
    RaketaSettingsChanged,
    WayOfWorkingChosen,
)
from app.modules.clubs.domain.events import (
    ClubAccountOpened,
    ClubDetailsChanged,
    ClubRegistered,
)

NOW = datetime(2026, 9, 25, tzinfo=timezone.utc)
CLUB = uuid4()

EVENTS = [
    ClubRegistered(
        club_id=CLUB,
        name="Ogrody 33",
        district="Grzegórzki",
        city="Kraków",
        sports=("PADEL", "TENNIS"),
        latitude=50.0612345,
        longitude=19.9587654,
        occurred_at=NOW,
    ),
    ClubDetailsChanged(
        club_id=CLUB,
        name="Ogrody 33",
        district="Grzegórzki",
        city="Kraków",
        sports=("TENNIS",),
        latitude=50.0631,
        longitude=19.9612,
        occurred_at=NOW,
    ),
    ClubAccountOpened(
        account_id=uuid4(),
        club_id=CLUB,
        email="desk@ogrody33.pl",
        password_hash="$2b$12$notarealhash",
        occurred_at=NOW,
    ),
]


def _codec() -> JsonEventCodec:
    catalog = EventCatalog()
    register_club_events(catalog)
    return JsonEventCodec(catalog)


@pytest.mark.parametrize("event", EVENTS, ids=lambda event: type(event).__name__)
def test_an_event_decodes_back_into_the_event_that_was_appended(event):
    codec = _codec()
    encoded = codec.encode(event)

    decoded = codec.decode(
        SerializedEventEnvelope(
            id=uuid4(),
            event_type=encoded.event_type,
            schema_version=encoded.schema_version,
            payload=encoded.payload,
            occurred_at=event.occurred_at,
        )
    )

    assert decoded == event


def test_each_event_is_filed_under_its_own_name_in_the_clubs_namespace():
    names = [_codec().encode(event).event_type for event in EVENTS]

    assert names == [
        "clubs.club_registered",
        "clubs.club_details_changed",
        "clubs.club_account_opened",
    ]


@pytest.mark.parametrize("event_cls", [ClubRegistered, ClubDetailsChanged])
def test_the_club_s_own_stream_carries_no_credential(event_cls):
    carried = {field.name for field in fields(event_cls)}

    assert not carried & {"email", "password", "password_hash"}


# --------------------------------------------------------------------------- #
# Club courts (#535)
# --------------------------------------------------------------------------- #

COURT = uuid4()

COURT_EVENTS = [
    CourtAdded(
        club_id=CLUB,
        court_id=COURT,
        name="Kort centralny",
        sport="TENNIS",
        indoor=False,
        occurred_at=NOW,
    ),
    CourtChanged(
        club_id=CLUB,
        court_id=COURT,
        name="Court 1",
        sport="PADEL",
        indoor=True,
        occurred_at=NOW,
    ),
    CourtSwitchedOff(club_id=CLUB, court_id=COURT, occurred_at=NOW),
    CourtSwitchedOn(club_id=CLUB, court_id=COURT, occurred_at=NOW),
    CourtRemoved(club_id=CLUB, court_id=COURT, occurred_at=NOW),
    RaketaHoursSet(
        club_id=CLUB, court_id=COURT, hours=("2:18", "2:19", "6:9"), occurred_at=NOW
    ),
    ExceptionAdded(
        club_id=CLUB,
        exception_id=uuid4(),
        court_ids=(COURT, uuid4()),
        first_day="2026-10-12",
        last_day="2026-10-12",
        from_hour=9,
        until_hour=12,
        reason="Repair",
        occurred_at=NOW,
    ),
    ExceptionAdded(
        club_id=CLUB,
        exception_id=uuid4(),
        court_ids=None,
        first_day="2026-10-04",
        last_day="2026-10-05",
        from_hour=None,
        until_hour=None,
        reason="Tournament",
        occurred_at=NOW,
    ),
    ExceptionRemoved(club_id=CLUB, exception_id=uuid4(), occurred_at=NOW),
    PricesSet(
        club_id=CLUB,
        sport="PADEL",
        price_grosze=120_00,
        bands=("WEEKDAYS:17:22:14000", "WEEKEND:7:23:14000"),
        occurred_at=NOW,
    ),
    PricesSet(
        club_id=CLUB, sport="TENNIS", price_grosze=None, bands=(), occurred_at=NOW
    ),
    WayOfWorkingChosen(club_id=CLUB, way="ON_REQUEST", occurred_at=NOW),
    RaketaSettingsChanged(
        club_id=CLUB,
        release_lead_days=3,
        cut_off_hours=24,
        minimum_notice_hours=2,
        time_to_confirm_minutes=30,
        other_clubs_courts=True,
        other_clubs_within_km=15,
        occurred_at=NOW,
    ),
    RaketaPaused(club_id=CLUB, occurred_at=NOW),
    RaketaResumed(club_id=CLUB, occurred_at=NOW),
]


@pytest.mark.parametrize("event", COURT_EVENTS, ids=lambda event: type(event).__name__)
def test_a_club_courts_event_decodes_back_into_the_event_that_was_appended(event):
    codec = _codec()
    encoded = codec.encode(event)

    decoded = codec.decode(
        SerializedEventEnvelope(
            id=uuid4(),
            event_type=encoded.event_type,
            schema_version=encoded.schema_version,
            payload=encoded.payload,
            occurred_at=event.occurred_at,
        )
    )

    assert decoded == event


def test_the_club_courts_events_are_filed_in_the_clubs_namespace_at_version_one():
    encoded = [_codec().encode(event) for event in COURT_EVENTS]

    assert [(row.event_type, row.schema_version) for row in encoded] == [
        ("clubs.court_added", 1),
        ("clubs.court_changed", 1),
        ("clubs.court_switched_off", 1),
        ("clubs.court_switched_on", 1),
        ("clubs.court_removed", 1),
        ("clubs.raketa_hours_set", 1),
        ("clubs.exception_added", 1),
        ("clubs.exception_added", 1),
        ("clubs.exception_removed", 1),
        ("clubs.prices_set", 1),
        ("clubs.prices_set", 1),
        ("clubs.way_of_working_chosen", 1),
        ("clubs.raketa_settings_changed", 1),
        ("clubs.raketa_paused", 1),
        ("clubs.raketa_resumed", 1),
    ]
