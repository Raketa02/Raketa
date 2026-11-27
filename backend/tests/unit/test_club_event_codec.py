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
from app.application.ports.events import EventDecodingError
from app.infrastructure.events.json_event_codec import JsonEventCodec
from app.modules.clubs.application.event_subscriptions import register_club_events
from app.modules.clubs.domain.club_courts import ClubCourts
from app.modules.clubs.domain.club_courts_events import (
    CourtAdded,
    CourtChanged,
    CourtRemoved,
    CourtSwitchedOff,
    CourtSwitchedOn,
    ExceptionAdded,
    ExceptionRemoved,
    PricesSet,
    RakietaHoursSet,
    RakietaPaused,
    RakietaResumed,
    RakietaSettingsChanged,
)
from app.modules.clubs.domain.rakieta_terms import OtherClubsCourts
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
    RakietaHoursSet(
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
    RakietaSettingsChanged(
        club_id=CLUB,
        release_lead_days=3,
        cut_off_hours=24,
        other_clubs_courts=True,
        other_clubs_within_km=15,
        occurred_at=NOW,
    ),
    RakietaPaused(club_id=CLUB, occurred_at=NOW),
    RakietaResumed(club_id=CLUB, occurred_at=NOW),
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


def test_the_club_courts_events_are_filed_in_the_clubs_namespace():
    encoded = [_codec().encode(event) for event in COURT_EVENTS]

    assert [(row.event_type, row.schema_version) for row in encoded] == [
        ("clubs.court_added", 1),
        ("clubs.court_changed", 1),
        ("clubs.court_switched_off", 1),
        ("clubs.court_switched_on", 1),
        ("clubs.court_removed", 1),
        ("clubs.rakieta_hours_set", 1),
        ("clubs.exception_added", 1),
        ("clubs.exception_added", 1),
        ("clubs.exception_removed", 1),
        ("clubs.prices_set", 1),
        ("clubs.prices_set", 1),
        # Version 2 since the minimum notice and the time to confirm went
        # (#670), and 3 since other clubs' courts are on by default (#746).
        ("clubs.rakieta_settings_changed", 3),
        ("clubs.rakieta_paused", 1),
        ("clubs.rakieta_resumed", 1),
    ]


def test_the_clubs_file_history_under_these_names_and_no_other():
    """The whole register, not only the names an event is written under. The
    settings, the hours and pausing were renamed with the brand (#892, ADR-0211)
    and the local store was reset, so no event answers to a name from before
    the rename: a registration under one would be one more pair here."""

    catalog = EventCatalog()
    register_club_events(catalog)
    registered = [
        (contract.name, contract.version)
        for contract in map(catalog.contract_for, catalog.registered_classes())
    ]

    assert registered == [
        ("clubs.club_registered", 1),
        ("clubs.club_details_changed", 1),
        ("clubs.club_account_opened", 1),
        ("clubs.club_account_password_changed", 1),
        ("clubs.court_added", 1),
        ("clubs.court_changed", 1),
        ("clubs.court_switched_off", 1),
        ("clubs.court_switched_on", 1),
        ("clubs.court_removed", 1),
        ("clubs.rakieta_hours_set", 1),
        ("clubs.exception_added", 1),
        ("clubs.exception_removed", 1),
        ("clubs.prices_set", 1),
        # Decode-only: a v2 row reads other clubs' courts on (#746).
        ("clubs.rakieta_settings_changed", 2),
        ("clubs.rakieta_settings_changed", 3),
        ("clubs.rakieta_paused", 1),
        ("clubs.rakieta_resumed", 1),
        ("clubs.payments_account_opened", 1),
        ("clubs.payments_status_changed", 1),
    ]


def test_the_way_of_working_has_no_reader_any_more():
    """Only Rakieta is the one way (#670; ``docs/adr/0196`` §1): the choice went
    with Instant and On request, and its name is given no class to answer to —
    the local store is reset with the removal."""

    with pytest.raises(EventDecodingError):
        _codec().decode(
            SerializedEventEnvelope(
                id=uuid4(),
                event_type="clubs.way_of_working_chosen",
                schema_version=1,
                payload={
                    "club_id": str(CLUB),
                    "way": "INSTANT",
                    "occurred_at": NOW.isoformat(),
                },
                occurred_at=NOW,
            )
        )


def test_settings_saved_under_version_1_are_refused_rather_than_misread():
    """Version 1 carried the minimum notice and the time to confirm, and *We
    check players in* before them. It is deliberately unreadable: nothing ran
    anywhere but ``local``, whose store is reset with the removal."""

    with pytest.raises(EventDecodingError):
        _codec().decode(
            SerializedEventEnvelope(
                id=uuid4(),
                event_type="clubs.rakieta_settings_changed",
                schema_version=1,
                payload={
                    "club_id": str(CLUB),
                    "release_lead_days": 3,
                    "cut_off_hours": 24,
                    "minimum_notice_hours": 2,
                    "time_to_confirm_minutes": 30,
                    "other_clubs_courts": False,
                    "other_clubs_within_km": 10,
                    "check_in": None,
                    "occurred_at": NOW.isoformat(),
                },
                occurred_at=NOW,
            )
        )


def _settings_under_version_2(*, other_clubs_courts: bool) -> SerializedEventEnvelope:
    return SerializedEventEnvelope(
        id=uuid4(),
        event_type="clubs.rakieta_settings_changed",
        schema_version=2,
        payload={
            "club_id": str(CLUB),
            "release_lead_days": 2,
            "cut_off_hours": 12,
            "other_clubs_courts": other_clubs_courts,
            "other_clubs_within_km": 15,
            "occurred_at": NOW.isoformat(),
        },
        occurred_at=NOW,
    )


@pytest.mark.parametrize("recorded", [False, True])
def test_settings_saved_under_version_2_read_other_clubs_courts_on(recorded):
    """``docs/adr/0202`` §7 (#746): the switch is **on by default, for existing
    clubs too**. Version 2 was written while off was the default and the form
    saved every field, so its *off* cannot be told from a default nobody
    touched: it reads on, at the distance it kept, and everything else as it
    was saved."""

    decoded = _codec().decode(_settings_under_version_2(other_clubs_courts=recorded))
    settings = ClubCourts.from_history(CLUB, [decoded]).settings

    assert settings.other_clubs_courts == OtherClubsCourts(offered=True, within_km=15)
    assert (settings.release_lead_days, settings.cut_off_hours) == (2, 12)


def test_settings_saved_under_version_3_keep_other_clubs_courts_off():
    """From version 3 *off* is a club's own choice, and is read as one."""

    saved = RakietaSettingsChanged(
        club_id=CLUB,
        release_lead_days=2,
        cut_off_hours=12,
        other_clubs_courts=False,
        other_clubs_within_km=15,
        occurred_at=NOW,
    )
    codec = _codec()
    encoded = codec.encode(saved)
    decoded = codec.decode(
        SerializedEventEnvelope(
            id=uuid4(),
            event_type=encoded.event_type,
            schema_version=encoded.schema_version,
            payload=encoded.payload,
            occurred_at=NOW,
        )
    )

    assert ClubCourts.from_history(CLUB, [decoded]).settings.other_clubs_courts == (
        OtherClubsCourts(offered=False, within_km=15)
    )
