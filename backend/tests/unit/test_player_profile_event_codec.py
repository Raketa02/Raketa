"""Every Player profile event survives the round trip through storage.

A durable name is a **published contract**, so two things are asserted: that each
event has one, and that an event decoded out of the store equals the event that
was appended. The second is what the collection fields need — JSON has arrays and
not tuples, so an event that did not normalise its own would come back holding
lists and fold differently on replay than it did on the way in.
"""

from __future__ import annotations

import pytest

from app.application.events import EventCatalog
from app.application.events.envelope import SerializedEventEnvelope
from app.application.ports.events import EventDecodingError
from app.modules.player_profile.application.event_subscriptions import (
    PROFILE_CREATED_VERSION,
    register_player_profile_events,
)
from app.modules.player_profile.domain.events import (
    GenderChanged,
    GenderPreferenceChanged,
    IntroChanged,
    IntroWritten,
    LocationChanged,
    PhotosChanged,
    PlayerProfileCreated,
    PlayIntentDeclared,
    SocialTagsChanged,
    WeeklyHoursSet,
)
from app.shared.ids import new_uuid
from tests.unit.fake_event_store import domain_event_codec, utc

PLAYER = new_uuid()
PHOTO = new_uuid()
AT = utc(2026, 8, 25)

EVENTS = [
    PlayerProfileCreated(
        player_id=PLAYER,
        social_tags=("PLAYS_TO_WIN", "HERE_TO_IMPROVE"),
        photo_ids=(str(PHOTO),),
        weekly_hours=("2:19",),
        latitude=51.51,
        longitude=-0.13,
        idempotency_key="commit-1",
        occurred_at=AT,
        gender="WOMAN",
        gender_preference="WOMEN_ONLY",
    ),
    SocialTagsChanged(
        player_id=PLAYER, social_tags=("QUIET_AND_FOCUSED",), occurred_at=AT
    ),
    PhotosChanged(player_id=PLAYER, photo_ids=(str(PHOTO),), occurred_at=AT),
    WeeklyHoursSet(player_id=PLAYER, weekly_hours=(), occurred_at=AT),
    LocationChanged(player_id=PLAYER, latitude=48.85, longitude=2.35, occurred_at=AT),
    GenderChanged(player_id=PLAYER, gender="MAN", occurred_at=AT),
    GenderPreferenceChanged(player_id=PLAYER, gender_preference="ANY", occurred_at=AT),
    IntroWritten(player_id=PLAYER, intro="Moved from Wrocław in May.", occurred_at=AT),
    IntroChanged(
        player_id=PLAYER, intro="Will travel for a hard game.", occurred_at=AT
    ),
    PlayIntentDeclared(
        player_id=PLAYER,
        sport="PADEL",
        intent="COMPETITIVE",
        surface="RATING_TAIL",
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


def test_a_withdrawn_intro_decodes_back_as_the_absence_it_recorded():
    """The one event here whose payload carries a ``null`` on purpose: a
    withdrawal is ``intro: None``, and it has to come back as ``None`` rather
    than as a missing key the class would refuse or a string it would fold."""

    codec = domain_event_codec()
    withdrawn = IntroChanged(player_id=PLAYER, intro=None, occurred_at=AT)

    encoded = codec.encode(withdrawn)
    decoded = codec.decode(
        SerializedEventEnvelope(
            id=new_uuid(),
            event_type=encoded.event_type,
            schema_version=encoded.schema_version,
            payload=encoded.payload,
            occurred_at=AT,
        )
    )

    assert encoded.event_type == "player_profile.intro_changed"
    assert decoded == withdrawn
    assert decoded.intro is None


def test_every_event_this_context_records_has_a_durable_name():
    """A class with no contract raises at encode time — which would be the first
    write after somebody added an event and forgot to register it."""

    codec = domain_event_codec()

    names = {codec.encode(event).event_type for event in EVENTS}

    assert len(names) == len(EVENTS), "one name per event, none shared"
    assert all(name.startswith("player_profile.") for name in names)


def test_the_creating_event_is_written_under_version_3_without_a_radius():
    """``docs/adr/0189`` §5 made the week hours (version 2), and #581 took the
    search radius out (version 3) — each a change to the wire shape, versioned
    as one rather than reinterpreted."""

    encoded = domain_event_codec().encode(EVENTS[0])

    assert encoded.event_type == "player_profile.created"
    assert encoded.schema_version == 3
    assert encoded.payload["weekly_hours"] == ["2:19"]
    assert "availability" not in encoded.payload
    assert "search_radius_km" not in encoded.payload


def test_a_creation_with_a_radius_written_under_version_2_is_refused():
    """Version 2 is unreadable for version 1's reason (``domain/events.py``):
    nothing ran anywhere but ``local``, whose store is reset with the change,
    and a row written under an old shape is a decoding error rather than a
    profile folded wrongly."""

    written_while_the_radius_was_asked = {
        "player_id": str(PLAYER),
        "social_tags": ["PLAYS_TO_WIN", "HERE_TO_IMPROVE"],
        "photo_ids": [str(PHOTO)],
        "weekly_hours": ["2:19"],
        "latitude": 51.51,
        "longitude": -0.13,
        "search_radius_km": 10,
        "idempotency_key": "commit-1",
        "occurred_at": AT.isoformat(),
    }

    with pytest.raises(EventDecodingError):
        domain_event_codec().decode(
            SerializedEventEnvelope(
                id=new_uuid(),
                event_type="player_profile.created",
                schema_version=2,
                payload=written_while_the_radius_was_asked,
                occurred_at=AT,
            )
        )


@pytest.mark.parametrize(
    "event_type, payload",
    [
        (
            "player_profile.search_radius_changed",
            {"search_radius_km": 25},
        ),
        (
            "player_profile.proposals_opt_in_answered",
            {"accepted": True, "copy_version": "v1", "surface": "PROFILE"},
        ),
    ],
)
def test_the_radius_and_the_opt_in_have_no_reader_any_more(event_type, payload):
    """Both went with the ranking that read them (#581), and neither name is
    given a class to answer to."""

    with pytest.raises(EventDecodingError):
        domain_event_codec().decode(
            SerializedEventEnvelope(
                id=new_uuid(),
                event_type=event_type,
                schema_version=1,
                payload={
                    "player_id": str(PLAYER),
                    **payload,
                    "occurred_at": AT.isoformat(),
                },
                occurred_at=AT,
            )
        )


def test_a_week_of_parts_written_under_version_1_is_refused_rather_than_misread():
    """Version 1 is deliberately unreadable: nothing ran anywhere but
    ``local``, whose database is disposable, and a row written under the old
    shape is a decoding error rather than a week folded wrongly."""

    written_before_the_week_became_hours = {
        "player_id": str(PLAYER),
        "social_tags": ["PLAYS_TO_WIN", "HERE_TO_IMPROVE"],
        "photo_ids": [str(PHOTO)],
        "availability": ["2:EVENING"],
        "latitude": 51.51,
        "longitude": -0.13,
        "search_radius_km": 10,
        "idempotency_key": "commit-1",
        "occurred_at": AT.isoformat(),
    }

    with pytest.raises(EventDecodingError):
        domain_event_codec().decode(
            SerializedEventEnvelope(
                id=new_uuid(),
                event_type="player_profile.created",
                schema_version=1,
                payload=written_before_the_week_became_hours,
                occurred_at=AT,
            )
        )


def test_the_part_of_day_week_edit_has_no_reader_any_more():
    """``player_profile.availability_changed`` was replaced by
    ``player_profile.weekly_hours_set``, not given a second class to answer to."""

    codec = domain_event_codec()

    assert codec.encode(EVENTS[3]).event_type == "player_profile.weekly_hours_set"
    with pytest.raises(EventDecodingError):
        codec.decode(
            SerializedEventEnvelope(
                id=new_uuid(),
                event_type="player_profile.availability_changed",
                schema_version=1,
                payload={
                    "player_id": str(PLAYER),
                    "availability": ["2:EVENING"],
                    "occurred_at": AT.isoformat(),
                },
                occurred_at=AT,
            )
        )


def test_a_play_intent_declaration_carries_the_pair_and_never_its_stream_id():
    """The id is a function of ``(player, sport)``, so storing it would be a
    second copy of one fact — and the copy the row holds is the one that would be
    believed if the two ever disagreed."""

    payload = domain_event_codec().encode(EVENTS[-1]).payload

    assert set(payload) == {
        "player_id",
        "sport",
        "intent",
        "surface",
        "occurred_at",
    }
    assert payload["sport"] == "PADEL"


def test_a_creating_event_carries_no_precise_location():
    """Two coarse floats and nothing beside them — there is no field a device's
    own reading could have been recorded in."""

    payload = domain_event_codec().encode(EVENTS[0]).payload

    assert payload["latitude"] == 51.51
    assert payload["longitude"] == -0.13


def test_a_durable_name_cannot_be_claimed_by_a_second_class():
    """The guard that keeps a name meaning one thing forever. Renaming the Python
    class is free; letting another class answer to `player_profile.created` would
    make every row already in the store decode into the wrong shape."""

    catalog = EventCatalog()
    register_player_profile_events(catalog)

    class Impostor:
        occurred_at = AT

    with pytest.raises(ValueError):
        catalog.register(
            Impostor, name="player_profile.created", version=PROFILE_CREATED_VERSION
        )
