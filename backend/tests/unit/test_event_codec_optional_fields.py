"""An optional id on an event decodes as an id, not as the string it was stored as.

**The failure this pins is silent, which is why it is pinned.** The codec
coerces a stored string back to a ``UUID`` by comparing the field's type hint
against ``UUID`` — and ``UUID | None`` is not ``UUID``, so for an optional field
the coercion simply did not fire. Nothing raised. The event reconstructed
perfectly, carrying a ``str`` where a ``UUID`` had been written, and every
comparison against the value that wrote it came back false: a replayed aggregate
quietly disagreeing with the one that saved it, in a context whose whole point
is that the record is the answer.

It had never fired because no event in the tree carried an optional id until
Money's movements did (``Raketa02/Raketa#69``) — a party may be the platform,
which has no id, and a debt payment names no seat.

Written against a **synthetic** event rather than a real one, because the claim
is about the codec and not about any context's stream: a test tied to
``MovementRecorded`` would go green the day somebody made that field required
for an unrelated reason.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.application.events.catalog import EventCatalog
from app.application.events.envelope import SerializedEventEnvelope
from app.infrastructure.events.json_event_codec import JsonEventCodec

NOW = datetime(2026, 8, 24, tzinfo=timezone.utc)


@dataclass(frozen=True)
class _WithOptionalIds:
    required_id: UUID
    optional_id: UUID | None
    optional_when: datetime | None
    absent_id: UUID | None
    occurred_at: datetime


def _codec() -> JsonEventCodec:
    catalog = EventCatalog()
    catalog.register(_WithOptionalIds, name="test.with_optional_ids", version=1)
    return JsonEventCodec(catalog)


def _round_trip(event: _WithOptionalIds) -> _WithOptionalIds:
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
    assert isinstance(decoded, _WithOptionalIds)
    return decoded


def test_an_optional_uuid_comes_back_as_a_uuid() -> None:
    event = _WithOptionalIds(
        required_id=uuid4(),
        optional_id=uuid4(),
        optional_when=NOW,
        absent_id=None,
        occurred_at=NOW,
    )

    decoded = _round_trip(event)

    assert isinstance(decoded.optional_id, UUID)
    assert decoded.optional_id == event.optional_id
    # The whole event, not only the field: equality is what an aggregate's
    # replay actually rests on.
    assert decoded == event


def test_an_optional_datetime_comes_back_as_a_datetime() -> None:
    event = _WithOptionalIds(
        required_id=uuid4(),
        optional_id=None,
        optional_when=NOW,
        absent_id=None,
        occurred_at=NOW,
    )

    decoded = _round_trip(event)

    assert isinstance(decoded.optional_when, datetime)
    assert decoded == event


def test_an_absent_optional_stays_absent() -> None:
    event = _WithOptionalIds(
        required_id=uuid4(),
        optional_id=None,
        optional_when=None,
        absent_id=None,
        occurred_at=NOW,
    )

    decoded = _round_trip(event)

    assert decoded.optional_id is None
    assert decoded.optional_when is None
    assert decoded == event


def test_a_required_id_is_unaffected() -> None:
    """The control: the case that always worked still works."""

    event = _WithOptionalIds(
        required_id=uuid4(),
        optional_id=None,
        optional_when=None,
        absent_id=None,
        occurred_at=NOW,
    )

    assert isinstance(_round_trip(event).required_id, UUID)
