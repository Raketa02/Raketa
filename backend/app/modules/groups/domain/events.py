"""The Group's stream.

``docs/adr/0183`` §1 lists the whole of what a group's stream will say. This
build writes the first two: a player group is **created**, and somebody **joins**
it. Requests, leaving, ownership, edits, official groups and handovers are each
their own event and arrive with the tickets that need them (#505, #506, #509,
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
