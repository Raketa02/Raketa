"""The Friends context's durable events — twelve, and what each carries.

Primitive fields only, so the wire format survives a refactor of the Python
types: the two players as their uuids, the enums as their values. **Every event
names both players**, so *every friendship this player appears in* is a
question the log itself can answer, as a Block's is.

**A Friend link's two events name its owner alone** (#748): the code it carries
is an address posted to chats, no secret (``domain/link.py``).

**An ask for a level, its answer and its setting aside name the two friends
too** (#749, #764): who asked, and the friend asked to get a level.

**None of them is a notification by itself.** They ride the outbox because every
event does; Notifications tells a request to the person asked, *friends made*
to whoever asked (both, for a crossed request), an ask for a level to the friend
asked and its answer to the asker, and nothing else here is told to anybody —
an ask set aside least of all.
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
    #: Asked of somebody the requester shared no group with at asking (#773;
    #: ``docs/adr/0203`` §9): it counts towards the requester's daily limit.
    #: Decided at asking, because a group joined later must not uncount it.
    #: Defaulted, so every older row reads as uncounted — none could be.
    counted: bool = False


@dataclass(frozen=True)
class FriendRequestSetAside:
    """``friends.friend_request_set_aside`` v1 — *Not now*. The request stays
    open; the card leaves the reader's Home, and the requester is never told."""

    requester_id: UUID
    addressee_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class FriendRequestBroughtBack:
    """``friends.friend_request_brought_back`` v1 — the person asked opened the
    requester's Friend link (#748) while the request stood **set aside**: it is
    back on their Home, and nobody is told — they are the one who just opened
    it."""

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


@dataclass(frozen=True)
class FriendLinkMade:
    """``friends.friend_link_made`` v1 — the owner read their Friend link for
    the first time, and it was made: ``<public site>/f/<code>``."""

    owner_id: UUID
    code: str
    occurred_at: datetime


@dataclass(frozen=True)
class FriendLinkReplaced:
    """``friends.friend_link_replaced`` v1 — **New link**: ``code`` from now on,
    and ``replaced_code`` dead, never to lead anywhere again."""

    owner_id: UUID
    code: str
    replaced_code: str
    occurred_at: datetime


@dataclass(frozen=True)
class LevelAsked:
    """``friends.level_asked`` v1 — **Ask for a level** (#749; ``docs/adr/0202``
    §4): ``asker_id`` asked ``friend_id``, a friend with no level in ``sport``,
    to get one. ``group_id`` is the group whose picker it was asked from — what
    the answer opens. Once per asker, friend and sport, ever."""

    asker_id: UUID
    friend_id: UUID
    sport: str
    group_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class LevelAskSetAside:
    """``friends.level_ask_set_aside`` v1 — **Not now** on the ask's Home card
    (#764; ``docs/adr/0202`` §4's 2026-11-07 amendment): ``friend_id`` set aside
    ``asker_id``'s ask in ``sport``. Off the friend's Home and out of their bell,
    and **still waiting**: the friend's first level in the sport answers it as
    it answers any ask. Nobody is told, the asker least of all."""

    asker_id: UUID
    friend_id: UUID
    sport: str
    occurred_at: datetime


@dataclass(frozen=True)
class LevelGot:
    """``friends.level_got`` v1 — the ask answered: the rating context recorded
    ``friend_id``'s first level in ``sport``. Recorded once per ask, whether or
    not they are still friends; Notifications tells ``asker_id`` only while they
    are. ``group_id`` is the ask's."""

    asker_id: UUID
    friend_id: UUID
    sport: str
    group_id: UUID
    occurred_at: datetime
