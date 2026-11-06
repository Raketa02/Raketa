"""The Friends context's durable events — six, and what each carries.

Primitive fields only, so the wire format survives a refactor of the Python
types: the two players as their uuids, the enums as their values. **Every event
names both players**, so *every friendship this player appears in* is a
question the log itself can answer, as a Block's is.

**None of them is a notification by itself.** They ride the outbox because every
event does; Notifications tells a request to the person asked and *friends made*
to whoever asked (both, for a crossed request), and nothing else here is told
to anybody.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class FriendRequested:
    """``friends.friend_requested`` v1 — one player asked another.

    ``made_from`` is a ``RequestOrigin``; ``group_id`` and ``sport`` are the group
    and sport of the screen it was made on, when there was one — what the card
    on the other person's Home names.
    """

    requester_id: UUID
    addressee_id: UUID
    made_from: str
    group_id: UUID | None
    sport: str | None
    occurred_at: datetime
    #: Asked while the addressee had blocked the requester: open, and the
    #: requester reads *request sent* — and **never shown to the addressee**,
    #: not after an unblock either (``docs/adr/0202`` §2: *Tomek never sees
    #: it*). Defaulted, so the field adds nothing a row must carry.
    unseen: bool = False


@dataclass(frozen=True)
class FriendRequestSetAside:
    """``friends.friend_request_set_aside`` v1 — *Not now*. The request stays
    open; the card leaves the reader's Home, and the requester is never told."""

    requester_id: UUID
    addressee_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class FriendRequestCancelled:
    """``friends.friend_request_cancelled`` v1 — the requester took it back.
    Nobody is told."""

    requester_id: UUID
    addressee_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class FriendRequestCrossed:
    """``friends.friend_request_crossed`` v1 — a request made of somebody who had
    already asked the requester: the two crossed, and ``FriendsMade`` follows it
    in the same act. Where it was made is kept, as for any request."""

    requester_id: UUID
    addressee_id: UUID
    made_from: str
    group_id: UUID | None
    sport: str | None
    occurred_at: datetime


@dataclass(frozen=True)
class FriendsMade:
    """``friends.friends_made`` v1 — they are friends.

    ``requester_id`` asked first; ``addressee_id`` said yes (``how`` ``ACCEPTED``)
    or asked back (``CROSSED``).
    """

    requester_id: UUID
    addressee_id: UUID
    how: str
    occurred_at: datetime


@dataclass(frozen=True)
class FriendshipEnded:
    """``friends.friendship_ended`` v1 — whatever stood between them ended: the
    friendship, or an open request, or both cannot be — never two at once.

    ``how`` is ``REMOVED`` (a friend removed the other, silently) or ``BLOCKED``
    (one blocked the other, and a block ends a request as well as a friendship).
    ``ended_by`` is who removed or blocked.
    """

    ended_by: UUID
    other_id: UUID
    how: str
    occurred_at: datetime
