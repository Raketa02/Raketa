"""The Proposal stream as a **durable** contract.

Asserted against the real catalog registration, because the name and version a
row is filed under are what history is recorded as. One thing could go wrong
invisibly and has its own case: a version's names come back from JSON as a list
of strings, so a replayed version would name nobody a member's id is equal to.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.application.events import EventCatalog
from app.application.events.envelope import SerializedEventEnvelope
from app.infrastructure.events.json_event_codec import JsonEventCodec
from app.modules.proposals.application.event_subscriptions import (
    register_proposal_events,
)
from app.modules.proposals.domain.events import (
    CourtHourLost,
    GamesAndMoneySet,
    NoSaid,
    ProposalExpired,
    ProposalMade,
    ProposalWithdrawn,
    VersionDealt,
    YesSaid,
    YesWithdrawn,
)

NOW = datetime(2026, 10, 5, 6, tzinfo=timezone.utc)
PROPOSAL = uuid4()
PLAYER = uuid4()

EVENTS = [
    ProposalMade(
        proposal_id=PROPOSAL,
        pool_id=uuid4(),
        pool_kind="GROUP",
        origin="POST",
        poster_id=PLAYER,
        sport="PADEL",
        kind="FOR_FUN",
        club_id=uuid4(),
        start=datetime(2026, 10, 10, 15, tzinfo=timezone.utc),
        share_grosze=30_00,
        book_by=datetime(2026, 10, 10, 13, tzinfo=timezone.utc),
        occurred_at=NOW,
    ),
    VersionDealt(
        proposal_id=PROPOSAL, number=2, player_ids=(uuid4(), uuid4()), occurred_at=NOW
    ),
    YesSaid(proposal_id=PROPOSAL, player_id=PLAYER, occurred_at=NOW),
    NoSaid(proposal_id=PROPOSAL, player_id=PLAYER, occurred_at=NOW),
    YesWithdrawn(proposal_id=PROPOSAL, player_id=PLAYER, occurred_at=NOW),
    ProposalWithdrawn(proposal_id=PROPOSAL, withdrawn_by=PLAYER, occurred_at=NOW),
    ProposalExpired(proposal_id=PROPOSAL, occurred_at=NOW),
    CourtHourLost(proposal_id=PROPOSAL, occurred_at=NOW),
    GamesAndMoneySet(
        player_id=PLAYER, games_per_week=4, most_ill_pay_grosze=45_00, occurred_at=NOW
    ),
    GamesAndMoneySet(
        player_id=PLAYER, games_per_week=1, most_ill_pay_grosze=None, occurred_at=NOW
    ),
]


def _codec() -> JsonEventCodec:
    catalog = EventCatalog()
    register_proposal_events(catalog)
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


def test_each_event_is_filed_under_its_own_name_in_the_proposals_namespace():
    assert [_codec().encode(event).event_type for event in EVENTS] == [
        "proposals.proposal_made",
        "proposals.version_dealt",
        "proposals.yes_said",
        "proposals.no_said",
        "proposals.yes_withdrawn",
        "proposals.proposal_withdrawn",
        "proposals.proposal_expired",
        "proposals.court_hour_lost",
        "proposals.games_and_money_set",
        "proposals.games_and_money_set",
    ]
