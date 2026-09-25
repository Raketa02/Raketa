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
