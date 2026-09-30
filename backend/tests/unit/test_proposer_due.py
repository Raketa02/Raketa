"""What makes a pool due for the proposer's short tick (#540; the mechanics
§5.1: *a court frees up, a member joins, someone changes their hours*).

The subscriber **notes and never writes**: a joining is its group's pool, a
change to one player is every pool they are in, a swipe is its game's pool, and
a change to what a club sells is everywhere. A take hands over what was noted
and forgets it, so a change is dealt from once per tick.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.application.events import DeliveryContext
from app.modules.clubs.domain.club_courts_events import ExceptionAdded
from app.modules.groups.domain.events import GroupJoined, GroupLeft
from app.modules.player_profile.domain.events import WeeklyHoursSet
from app.modules.proposals.application.handlers import MarkDueForProposing
from app.modules.proposals.application.propose_games import Due, DueForProposing
from app.modules.proposals.domain.events import NoSaid

NOW = datetime(2026, 10, 5, 6, tzinfo=timezone.utc)
CONTEXT = DeliveryContext(event_id=uuid4(), attempt=1, occurred_at=NOW)


async def test_each_change_is_noted_where_it_matters_and_a_take_forgets_it():
    due = DueForProposing()
    marks = MarkDueForProposing(due)
    group, player, proposal = uuid4(), uuid4(), uuid4()

    await marks(
        GroupJoined(group_id=group, player_id=uuid4(), occurred_at=NOW), CONTEXT
    )
    await marks(
        WeeklyHoursSet(player_id=player, weekly_hours=("6:17",), occurred_at=NOW),
        CONTEXT,
    )
    await marks(
        NoSaid(proposal_id=proposal, player_id=player, occurred_at=NOW), CONTEXT
    )

    assert due.take() == Due(
        pools=frozenset({group}),
        players=frozenset({player}),
        proposals=frozenset({proposal}),
    )
    assert due.take() == Due()
    assert not Due().anything


async def test_a_change_to_what_a_club_sells_is_everywhere_and_leaving_is_nothing():
    due = DueForProposing()
    marks = MarkDueForProposing(due)

    # A leaver's yeses are withdrawn by their own subscriber; the proposer has
    # nothing to deal for somebody gone.
    await marks(
        GroupLeft(group_id=uuid4(), player_id=uuid4(), occurred_at=NOW), CONTEXT
    )
    assert not due.take().anything

    await marks(
        ExceptionAdded(
            club_id=uuid4(),
            exception_id=uuid4(),
            court_ids=None,
            first_day="2026-10-10",
            last_day="2026-10-10",
            from_hour=17,
            until_hour=18,
            reason="Repair",
            occurred_at=NOW,
        ),
        CONTEXT,
    )
    assert due.take() == Due(everywhere=True)
