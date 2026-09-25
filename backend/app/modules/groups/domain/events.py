"""The Group's stream.

``docs/adr/0183`` §1 lists the whole of what a group's stream will say. This
build writes five: a player group is **created**, somebody **joins** it, and on a
*People I approve* group somebody **asks** and the Owner **approves** or
**declines** (#505). Leaving, ownership, edits, official groups and handovers are
each their own event and arrive with the tickets that need them (#506, #509,
#510).

**Each kind is created by its own event**, because every rule that differs by
kind has to say so in its own words and none may be inferred from a null
(``docs/adr/0183`` §1): a player group names its Owner, and an official group
will name no such person.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class PlayerGroupCreated:
    """A player created a group at a home club — **and is its Owner and first
    member from this instant**, so there is no separate *joined* for them: the
    group has never existed without its creator in it.

    ``code`` is the one its link will carry for ever (``docs/adr/0183`` §4).
    """

    group_id: UUID
    name: str
    home_club_id: UUID
    join_policy: str
    owner_id: UUID
    code: str
    occurred_at: datetime


@dataclass(frozen=True)
class GroupJoined:
    """A player became a Group member. Recorded once per joining: joining a
    group you are already in records nothing (``docs/adr/0183`` §7)."""

    group_id: UUID
    player_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class JoinRequested:
    """A player asked to join a *People I approve* group, and their Join request
    waits for whoever answers it. **At most one waits per player per group**:
    asking again while waiting records nothing (``docs/adr/0183`` §7)."""

    group_id: UUID
    player_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class JoinRequestApproved:
    """The Owner approved a Join request — **and the person is a Group member
    from this instant**, so there is no separate *joined* beside it: approving
    is admitting, and one act is one event. ``approved_by`` is who answered,
    because ownership passes (#506) and the history should still say who let
    somebody in."""

    group_id: UUID
    player_id: UUID
    approved_by: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class JoinRequestDeclined:
    """The Owner declined a Join request. **Silent**: the request is gone, the
    person's relation to the group is *none* again and they may ask again, and
    nothing tells them (``docs/adr/0183`` §7). The stream remembers it; no read
    serves it."""

    group_id: UUID
    player_id: UUID
    declined_by: UUID
    occurred_at: datetime
