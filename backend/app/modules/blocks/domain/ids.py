"""Identity in the Blocks context: the ordered pair *is* the stream.

``ADR-0019``'s scheme, one dimension shorter than the Play intent
declaration's — ``uuid5`` over a namespace of this context's own, collapsing two
player ids into the id of the stream that records what passes between them
(``docs/adr/0095``).

**Ordered, and the order is the whole design.** ``block_id(a, b)`` and
``block_id(b, a)`` are two different streams, so *A blocked B* and *B blocked A*
are two independent records with two independent versions. A symmetric id —
sorting the pair before hashing — was the obvious alternative and it is exactly
the one-symmetric-edge shape ADR-0095 rejected: it makes unblock ambiguous the
moment both parties have blocked, and *both parties have blocked* is not an
exotic case.

**A concurrency control as much as a naming convenience.** Two blocks of the same
person that both read an empty stream compute the same id, collide on version 1
and the store rejects the loser. With a random id per call each would have minted
its own stream, and one pair would hold two blocks with no rule for which
answers — the failure mode this scheme exists to make impossible, and the reason
idempotence can be a question the aggregate answers about itself rather than a
table beside it.

Its own namespace, and never another aggregate's: two aggregates keyed on the
same pair would compute the same uuid, and the ``aggregate_type`` column would be
all that kept their streams apart. That is one column too few to hang a data
corruption on.
"""

from __future__ import annotations

from uuid import NAMESPACE_URL, UUID, uuid5

_BLOCK_NAMESPACE = uuid5(NAMESPACE_URL, "rakieta/block")


def block_id(blocker_id: UUID, blocked_id: UUID) -> UUID:
    """The deterministic event-stream id for one **ordered** pair.

    Guessable by anyone holding two player ids, and that leaks nothing: reading a
    block requires saying whose it is, and nothing in this module serves one back
    out to either party.
    """

    return uuid5(_BLOCK_NAMESPACE, f"{blocker_id}:{blocked_id}")
