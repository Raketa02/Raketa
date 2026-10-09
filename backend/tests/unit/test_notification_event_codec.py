"""The facts #621 and #622 add to Notifications' streams, as a **durable**
contract: a visit to the recent notices, filed under its own name; a notice of
the player's own act — defaulted rather than a version 2, so a notice given
before reads as nobody's own; and the deadline a notice names, defaulted so a
notice given before names none.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.application.events import EventCatalog
from app.application.events.envelope import SerializedEventEnvelope
from app.infrastructure.events.json_event_codec import JsonEventCodec
from app.modules.notifications.application.event_subscriptions import (
    register_notification_events,
)
from app.modules.notifications.domain.events import NoticeGiven, RecentNoticesOpened

NOW = datetime(2026, 10, 9, 10, tzinfo=timezone.utc)


def _codec() -> JsonEventCodec:
    catalog = EventCatalog()
    register_notification_events(catalog)
    return JsonEventCodec(catalog)


def _decoded(codec: JsonEventCodec, event_type: str, payload: dict):
    return codec.decode(
        SerializedEventEnvelope(
            id=uuid4(),
            event_type=event_type,
            schema_version=1,
            payload=payload,
            occurred_at=NOW,
        )
    )


def _given(*, own: bool, until: datetime | None = None) -> NoticeGiven:
    return NoticeGiven(
        notice_id=uuid4(),
        player_id=uuid4(),
        day="2026-10-09",
        kind="GAME_BOOKED",
        key="GAME_BOOKED:event",
        game_id=uuid4(),
        pool_id=uuid4(),
        sport="PADEL",
        game_kind="COMPETITIVE",
        club_id=uuid4(),
        starts_at=NOW,
        opens="BOOKING",
        amount_grosze=30_00,
        people=(),
        reason=None,
        occurred_at=NOW,
        own=own,
        until=until,
    )


def test_a_visit_is_filed_under_its_own_name_and_decodes_back():
    codec = _codec()
    opened = RecentNoticesOpened(player_id=uuid4(), occurred_at=NOW)

    encoded = codec.encode(opened)

    assert (encoded.event_type, encoded.schema_version) == (
        "notifications.recent_notices_opened",
        1,
    )
    assert _decoded(codec, encoded.event_type, encoded.payload) == opened


def test_a_notice_of_the_player_s_own_act_decodes_back_as_their_own():
    codec = _codec()
    given = _given(own=True)

    encoded = codec.encode(given)

    assert _decoded(codec, encoded.event_type, encoded.payload) == given


def test_a_notice_given_before_own_was_asked_is_nobody_s_own():
    codec = _codec()
    encoded = codec.encode(_given(own=True))
    older = {key: value for key, value in encoded.payload.items() if key != "own"}

    decoded = _decoded(codec, encoded.event_type, older)

    assert isinstance(decoded, NoticeGiven)
    assert decoded.own is False


def test_a_notice_keeps_the_deadline_it_names_and_one_given_before_names_none():
    codec = _codec()
    given = _given(own=False, until=datetime(2026, 10, 9, 19, 15, tzinfo=timezone.utc))
    encoded = codec.encode(given)
    older = {key: value for key, value in encoded.payload.items() if key != "until"}

    assert _decoded(codec, encoded.event_type, encoded.payload) == given
    decoded = _decoded(codec, encoded.event_type, older)
    assert isinstance(decoded, NoticeGiven)
    assert decoded.until is None
