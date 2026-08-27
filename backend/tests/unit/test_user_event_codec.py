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

from app.application.events import EventCatalog
from app.application.events.envelope import SerializedEventEnvelope
from app.infrastructure.events.json_event_codec import JsonEventCodec
from app.modules.users.application.event_subscriptions import register_user_events
from app.modules.users.domain.events import UserRegistered

NOW = datetime(2026, 8, 27, tzinfo=timezone.utc)

REGISTERED = UserRegistered(
    user_id=uuid4(),
    email="ada@example.com",
    nickname="ada",
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


def _envelope(payload: dict[str, object]) -> SerializedEventEnvelope:
    return SerializedEventEnvelope(
        id=uuid4(),
        event_type="users.user_registered",
        schema_version=1,
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
