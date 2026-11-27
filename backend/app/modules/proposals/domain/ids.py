"""Identity of a pick: **the game is its stream** (``docs/adr/0019``'s scheme,
as the Blocks context's pair is).

A pick is a court hour at a club, a kind and the people named on it, in one
pool and sport — and that is its id: ``uuid5`` over those, in a namespace of
this context's own. **A concurrency control as much as a name**: the proposer
runs in every API process with no lock (``docs/adr/0092``), so two processes
reaching the same batch compute the same id, collide on the stream's first
version, and the store refuses the loser — rather than dealing one game twice as
two cards. A post is its poster's act and keeps a random id.

The people are named **in the order dealt**, since that order is what a card
shows. The price is not part of it: a card's share is read off the club when it
is made, and the same people at the same hour are the same game whatever it
costs. The cost is named: a pick whose court hour was lost and later sold again
cannot be made twice for the same people — its stream is taken — and the next
batch deals them another.

**A card dealt first to the people of another names that one too** (#673): the
owed card is the closest game to the one a club's cancel took, so it may be the
same people at the same club and hour — the cancelled game's own id, whose
stream is taken — and only the game it is dealt after tells the two apart.
"""

from __future__ import annotations

from collections.abc import Sequence
from uuid import NAMESPACE_URL, UUID, uuid5

from app.engines.matchfit.core import SearchMode
from app.kernel import Instant, Sport

_PICK_NAMESPACE = uuid5(NAMESPACE_URL, "rakieta/proposal/pick")


def pick_id(
    *,
    pool_id: UUID,
    sport: Sport,
    kind: SearchMode,
    club_id: UUID,
    start: Instant,
    named: Sequence[UUID],
    after: UUID | None = None,
) -> UUID:
    """The stream id of the pick of these people at this court hour — dealt
    first to the people of ``after``, the card that lost its court hour or the
    game its club cancelled, when it is."""

    return uuid5(
        _PICK_NAMESPACE,
        ":".join(
            (
                str(pool_id),
                sport.value,
                kind.value,
                str(club_id),
                start.isoformat(),
                *(str(player) for player in named),
                *(() if after is None else (f"after={after}",)),
            )
        ),
    )
