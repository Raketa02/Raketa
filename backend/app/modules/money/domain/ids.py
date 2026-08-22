"""Identity in the Money context: one stream per player, derived not minted.

ADR-0055 fixes the stream key and the rule that makes it one:
``ledger_stream_id(player_id) = uuid5(namespace, player)``, matching
``skill_rating_id``'s rule under ADR-0019.

**Derived rather than stored, and that is a correctness property rather than a
convenience.** A minted-and-stored id needs a lookup table, and a lookup table
can be missing a row — at which point a second stream opens for a player who
already has one, and her balance is the fold of whichever half was read.
Deriving it means the pair *player → stream* has exactly one answer for ever,
found without a read, and two concurrent first movements collide on version 1 of
one stream rather than each minting a stream of its own (the defect
``assessment_stream_id`` was given the same shape to prevent, #35).

**A ledger is findable by player id, and stays findable after erasure.** That is
deliberate: the reconciliation has to be able to ask *what is this player's
position* the day after her account is closed, and ADR-0055 asks for the player
**party** to be pseudonymised, not for the stream to become unreachable — the
ledger refuses to forget. What identifies a person lives in Users and is erased
there; what is left here is an opaque id and a set of amounts.
"""

from __future__ import annotations

from typing import NewType
from uuid import NAMESPACE_URL, UUID, uuid5

#: A player, in Money's vocabulary. The identity *is* the ``UserId``, exactly as
#: it is in the rating context — a distinct name so the code reads in the
#: domain's words, and so the two have one place to diverge later.
PlayerId = NewType("PlayerId", UUID)

_LEDGER_NAMESPACE = uuid5(NAMESPACE_URL, "raketa/ledger")


def ledger_stream_id(player_id: UUID) -> UUID:
    """The deterministic event-stream id for one player's ledger."""

    return uuid5(_LEDGER_NAMESPACE, str(player_id))
