"""The refresh token's events as a durable contract, at version 2.

Version 1 carried ``user_id``; version 2 carries ``account_id`` and the
``audience`` (``docs/adr/0185`` §6). Asserted against the real registration:
each event reads back as the one appended, and a version-1 row is **refused**
rather than read — a token filed under the wrong kind of account is the failure
the version exists to prevent (``auth/application/event_subscriptions.py``).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.application.events import EventCatalog
from app.application.events.envelope import SerializedEventEnvelope
from app.application.ports.events import EventDecodingError
from app.infrastructure.events.json_event_codec import JsonEventCodec
from app.modules.auth.application.event_subscriptions import register_auth_events
from app.modules.auth.domain.events import (
    RefreshTokenIssued,
    RefreshTokenRevoked,
    RefreshTokenRotated,
)

NOW = datetime(2026, 9, 25, tzinfo=timezone.utc)

EVENTS = [
    RefreshTokenIssued(uuid4(), uuid4(), "jti", NOW + timedelta(days=1), NOW, "club"),
    RefreshTokenRevoked(uuid4(), uuid4(), "jti", "logout", NOW, "player_app"),
    RefreshTokenRotated(uuid4(), uuid4(), "old", uuid4(), "new", NOW, "club"),
]


def _codec() -> JsonEventCodec:
    catalog = EventCatalog()
    register_auth_events(catalog)
    return JsonEventCodec(catalog)


def _envelope(event_type: str, version: int, payload: dict) -> SerializedEventEnvelope:
    return SerializedEventEnvelope(
        id=uuid4(),
        event_type=event_type,
        schema_version=version,
        payload=payload,
        occurred_at=NOW,
    )


@pytest.mark.parametrize("event", EVENTS, ids=lambda event: type(event).__name__)
def test_each_event_is_written_at_version_2_and_reads_back(event):
    codec = _codec()
    encoded = codec.encode(event)

    assert encoded.schema_version == 2
    assert codec.decode(_envelope(encoded.event_type, 2, encoded.payload)) == event


def test_a_version_1_row_is_refused_rather_than_read():
    written_before_audiences = {
        "token_id": str(uuid4()),
        "user_id": str(uuid4()),
        "jti": "jti",
        "expires_at": NOW.isoformat(),
        "occurred_at": NOW.isoformat(),
    }

    with pytest.raises(EventDecodingError):
        _codec().decode(
            _envelope("auth.refresh_token_issued", 1, written_before_audiences)
        )
