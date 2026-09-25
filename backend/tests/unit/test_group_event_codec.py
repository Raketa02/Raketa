"""The Group's stream as a **durable** contract.

Asserted against the real catalog registration, because the name and version a
row is filed under are what history is recorded as — and a group's stream is
replayed on every join, so an event that did not read back as itself would be a
group that could not be joined again.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.application.events import EventCatalog
from app.application.events.envelope import SerializedEventEnvelope
from app.infrastructure.events.json_event_codec import JsonEventCodec
from app.modules.groups.application.event_subscriptions import register_group_events
from app.modules.groups.domain.events import (
    GroupDeleted,
    GroupJoined,
    GroupLeft,
    GroupRenamed,
    JoinPolicyChanged,
    JoinRequestApproved,
    JoinRequestDeclined,
    JoinRequested,
    OwnershipPassed,
    PlayerGroupCreated,
)

NOW = datetime(2026, 9, 25, tzinfo=timezone.utc)
GROUP = uuid4()
OWNER = uuid4()
ASKER = uuid4()

EVENTS = [
    PlayerGroupCreated(
        group_id=GROUP,
        name="my raketa group",
        home_club_id=uuid4(),
        join_policy="ANYONE",
        owner_id=OWNER,
        code="ab3de7fg",
        occurred_at=NOW,
    ),
    GroupJoined(group_id=GROUP, player_id=uuid4(), occurred_at=NOW),
    JoinRequested(group_id=GROUP, player_id=ASKER, occurred_at=NOW),
    JoinRequestApproved(
        group_id=GROUP, player_id=ASKER, approved_by=OWNER, occurred_at=NOW
    ),
    JoinRequestDeclined(
        group_id=GROUP, player_id=ASKER, declined_by=OWNER, occurred_at=NOW
    ),
    OwnershipPassed(group_id=GROUP, from_id=OWNER, to_id=ASKER, occurred_at=NOW),
    GroupLeft(group_id=GROUP, player_id=OWNER, occurred_at=NOW),
    GroupRenamed(
        group_id=GROUP, name="Kazimierz nights", renamed_by=ASKER, occurred_at=NOW
    ),
    JoinPolicyChanged(
        group_id=GROUP, join_policy="ANYONE", changed_by=ASKER, occurred_at=NOW
    ),
    GroupDeleted(group_id=GROUP, deleted_by=ASKER, occurred_at=NOW),
]


def _codec() -> JsonEventCodec:
    catalog = EventCatalog()
    register_group_events(catalog)
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


def test_each_event_is_filed_under_its_own_name_in_the_groups_namespace():
    encoded = [_codec().encode(event) for event in EVENTS]

    assert [(row.event_type, row.schema_version) for row in encoded] == [
        ("groups.player_group_created", 1),
        ("groups.group_joined", 1),
        ("groups.join_requested", 1),
        ("groups.join_request_approved", 1),
        ("groups.join_request_declined", 1),
        ("groups.ownership_passed", 1),
        ("groups.group_left", 1),
        ("groups.group_renamed", 1),
        ("groups.join_policy_changed", 1),
        ("groups.group_deleted", 1),
    ]
