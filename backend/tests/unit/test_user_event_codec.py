"""The users stream as a **durable** contract.

``UserRegistered`` gained the adult attestation as an appended field with a
default rather than as a new catalog version, which is only sound if a row
written before it still decodes. That is the whole argument for not needing a
migration, and it is asserted here rather than reasoned about.

Asserted against the **real catalog registration** — the codec the application
runs — because the name and version a row is filed under are what history is
recorded as, not the Python class name. Building the event in Python and reading
its default back proves nothing about a row already in the table.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.application.events import EventCatalog
from app.application.events.envelope import SerializedEventEnvelope
from app.application.ports.events import EventDecodingError
from app.infrastructure.events.json_event_codec import JsonEventCodec
from app.modules.users.application.event_subscriptions import register_user_events
from app.modules.users.domain.events import (
    AccountOpenedByInvitation,
    AccountOpenedByInvitationV1,
    AdultAttested,
    PasswordCleared,
    UserNamed,
    UserNamedV1,
    UserRegistered,
)

NOW = datetime(2026, 8, 27, tzinfo=timezone.utc)

REGISTERED = UserRegistered(
    user_id=uuid4(),
    email="ada@example.com",
    password_hash="$2b$12$notarealhash",
    authority="USER",
    is_admin=False,
    is_active=True,
    occurred_at=NOW,
    adult_attested=True,
)


def _codec() -> JsonEventCodec:
    """The codec the application runs, with the users context's events only.

    Kept narrow, the way the rating codec's tests keep theirs: a catalog with one
    context in it is what makes "this event has no contract" a failure this file
    can assert.
    """

    catalog = EventCatalog()
    register_user_events(catalog)
    return JsonEventCodec(catalog)


def _envelope(
    payload: dict[str, object],
    *,
    event_type: str = "users.user_registered",
    schema_version: int = 1,
) -> SerializedEventEnvelope:
    return SerializedEventEnvelope(
        id=uuid4(),
        event_type=event_type,
        schema_version=schema_version,
        payload=payload,
        occurred_at=NOW,
    )


def test_the_attestation_round_trips_under_the_unchanged_contract() -> None:
    codec = _codec()

    encoded = codec.encode(REGISTERED)

    # The name and version are unchanged: an appended default, not a new
    # contract. A version bump here would strand every row already written.
    assert encoded.event_type == "users.user_registered"
    assert encoded.schema_version == 1
    assert encoded.payload["adult_attested"] is True
    assert codec.decode(_envelope(encoded.payload)) == REGISTERED


def test_a_row_written_before_the_question_existed_still_decodes() -> None:
    # An account registered before this change, as its row actually looks: the
    # same event type and version, with the key simply absent. Derived by
    # dropping it from a current payload rather than typed in, so the rest of the
    # row cannot drift away from what the encoder really writes.
    codec = _codec()
    payload = dict(codec.encode(REGISTERED).payload)
    del payload["adult_attested"]

    decoded = codec.decode(_envelope(payload))

    # ``None`` and not ``False``. They are different facts — *nobody was ever
    # asked* against *somebody answered no* — and the second is a claim this
    # account never made. Reading absence as a refusal is the backfill ADR-0124
    # forbids, arrived at by accident.
    assert decoded == replace(REGISTERED, adult_attested=None)


def test_the_registration_carries_no_nickname() -> None:
    """Sign-up is credentials (``docs/adr/0171`` §2), and the row says so.

    Still v1: only one shape of this row will ever be stored, because only
    ``local`` runs and a reset seed is the migration. The version is what would
    have to move first the day a store outlives a change like this.
    """

    encoded = _codec().encode(REGISTERED)

    assert encoded.event_type == "users.user_registered"
    assert encoded.schema_version == 1
    assert "nickname" not in encoded.payload
    assert "name" not in encoded.payload


def test_the_naming_is_written_as_its_second_version_carrying_the_nickname_alone() -> (
    None
):
    """``users.user_named`` v2 (``docs/adr/0199`` §6): the Name is retired."""

    codec = _codec()
    named = UserNamed(user_id=REGISTERED.user_id, nickname="ada", occurred_at=NOW)

    encoded = codec.encode(named)

    assert encoded.event_type == "users.user_named"
    assert encoded.schema_version == 2
    assert encoded.payload["nickname"] == "ada"
    assert "name" not in encoded.payload
    assert (
        codec.decode(
            _envelope(encoded.payload, event_type="users.user_named", schema_version=2)
        )
        == named
    )


def test_a_naming_stored_as_the_first_version_still_decodes() -> None:
    """A v1 row carried a Name beside the nickname. It decodes to its own
    decode-only class, and the fold reads it with the name ignored."""

    decoded = _codec().decode(
        _envelope(
            {
                "user_id": str(REGISTERED.user_id),
                "name": "Ada Lovelace",
                "nickname": "ada",
                "occurred_at": NOW.isoformat(),
            },
            event_type="users.user_named",
        )
    )

    assert decoded == UserNamedV1(
        user_id=REGISTERED.user_id,
        name="Ada Lovelace",
        nickname="ada",
        occurred_at=NOW,
    )


def test_an_invitation_opening_stored_as_the_first_version_still_decodes() -> None:
    decoded = _codec().decode(
        _envelope(
            {
                "user_id": str(REGISTERED.user_id),
                "email": "marta@ogrody33.pl",
                "password_hash": "$2b$12$notarealhash",
                "name": "Marta Wójcik",
                "occurred_at": NOW.isoformat(),
            },
            event_type="users.account_opened_by_invitation",
        )
    )

    assert isinstance(decoded, AccountOpenedByInvitationV1)
    assert decoded.email == "marta@ogrody33.pl"


@pytest.mark.parametrize(
    "event_type", ["users.user_marked_as_tester", "users.user_unmarked_as_tester"]
)
def test_the_tester_mark_has_no_reader_any_more(event_type: str) -> None:
    """The mark went with the feature flags it fed (#581), and neither name is
    given a class to answer to: a stored row is a decoding error, and the local
    store is reset with the change."""

    with pytest.raises(EventDecodingError):
        _codec().decode(
            _envelope({"user_id": str(REGISTERED.user_id)}, event_type=event_type)
        )


@pytest.mark.parametrize(
    ("event", "event_type"),
    [
        (
            AdultAttested(user_id=REGISTERED.user_id, occurred_at=NOW),
            "users.adult_attested",
        ),
        (
            PasswordCleared(user_id=REGISTERED.user_id, occurred_at=NOW),
            "users.password_cleared",
        ),
    ],
)
def test_the_invitation_s_three_facts_round_trip_under_their_own_contracts(
    event: object, event_type: str
) -> None:
    """``docs/adr/0185`` grows the stream by an account an Invitation opened, an
    attestation given after it, and a password the club cleared — each filed
    under its own name."""

    codec = _codec()

    encoded = codec.encode(event)

    assert encoded.event_type == event_type
    assert encoded.schema_version == 1
    assert codec.decode(_envelope(encoded.payload, event_type=event_type)) == event


def test_an_account_an_invitation_opened_carries_no_player_name_and_no_nickname() -> (
    None
):
    """``users.account_opened_by_invitation`` v2 (``docs/adr/0199`` §4): the
    name the club typed is the Administrator's, and the account holds none."""

    codec = _codec()
    opened = AccountOpenedByInvitation(
        user_id=REGISTERED.user_id,
        email="marta@ogrody33.pl",
        password_hash="$2b$12$notarealhash",
        occurred_at=NOW,
    )

    encoded = codec.encode(opened)

    assert encoded.event_type == "users.account_opened_by_invitation"
    assert encoded.schema_version == 2
    assert (
        codec.decode(
            _envelope(
                encoded.payload,
                event_type="users.account_opened_by_invitation",
                schema_version=2,
            )
        )
        == opened
    )
    assert "name" not in encoded.payload
    assert "nickname" not in encoded.payload
    assert "adult_attested" not in encoded.payload
