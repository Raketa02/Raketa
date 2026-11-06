"""Identity in the Friends context: the **unordered** pair is the stream.

``uuid5`` over a namespace of this context's own, over the two player ids
**sorted** — the opposite choice from a Block's ordered pair, and for the
opposite reason. A block is directed so that one unblock never lifts the other;
a friendship is one fact about two people, and the two requests that could
stand between them are exclusive (a crossed request makes friends at once), so
there is nothing a second stream could hold that the first does not.

**A concurrency control too.** Two first requests between one pair — or two
that cross at one instant — both read an empty stream, compute the same id,
collide on version 1, and the store rejects the loser.

Its own namespace, never a Block's: two aggregates keyed on the same pair would
compute the same uuid.

**A Friend link is one stream per player**, ``uuid5`` over a namespace of its
own and the owner's id — never the player's id itself, which other aggregates'
streams are keyed on. Two first reads at once collide on version 1, as two
first requests do.
"""

from __future__ import annotations

from uuid import NAMESPACE_URL, UUID, uuid5

_FRIENDSHIP_NAMESPACE = uuid5(NAMESPACE_URL, "raketa/friendship")
_FRIEND_LINK_NAMESPACE = uuid5(NAMESPACE_URL, "raketa/friend-link")


def ordered_pair(first: UUID, second: UUID) -> tuple[UUID, UUID]:
    """The pair in the one order its stream is filed under."""

    return (first, second) if str(first) <= str(second) else (second, first)


def friendship_id(first: UUID, second: UUID) -> UUID:
    """The stream of whatever passes between these two, whichever way round."""

    low, high = ordered_pair(first, second)
    return uuid5(_FRIENDSHIP_NAMESPACE, f"{low}:{high}")


def friend_link_id(owner: UUID) -> UUID:
    """The stream of one player's Friend link."""

    return uuid5(_FRIEND_LINK_NAMESPACE, str(owner))
