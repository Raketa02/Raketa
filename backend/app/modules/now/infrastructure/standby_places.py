"""``StandbyPlaces``: which matches the viewer is queued for. **Ships dark.**

``NotOnStandby`` is one of the eight eligibility rules both ranked shelves
evaluate, and it needs a set to test against. **Standby has no store anywhere in
the product**: ``kernel.Viewer`` carries an ``on_standby`` flag that nothing
populates, there is no table, no port and no join operation, and the queue is a
membership the departure route and the invitation cascade will create
(``Raketa02/Raketa#81``, ``#82``). So the honest answer today is the empty set,
for every player, always.

**An empty adapter rather than a missing rule**, and the two are not the same
thing the day the store lands. A missing rule is a screen suggesting a player the
match she is already queued for — a defect nothing would catch, found by somebody
reading the pipeline months later. An empty adapter is one line in the
composition root, and the rule above it is already written, already evaluated and
already tested.

This is the shape ``PlayHistory`` and *Recently viewed* already take in this
product: a fact declared, reported as absent, and never fabricated.
"""

from __future__ import annotations

from uuid import UUID


class NoStandbyPlaces:
    """Nobody is on standby for anything, because nowhere records that they are."""

    async def for_player(self, player_id: UUID) -> frozenset[UUID]:
        return frozenset()
