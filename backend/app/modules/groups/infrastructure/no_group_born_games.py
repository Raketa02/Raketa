"""``GroupBornGames`` while no group can pick a game (``docs/adr/0183`` §11,
§13): nought, for every group.

**Not a placeholder for a number somebody forgot to compute.** A group picks no
games, posts none and books no courts in this build, so *games born in this
group* is truly none — and the club's *Games* column says so, rather than
counting games two members arranged elsewhere, which it would read as the
group's work. The day a group can pick a game, an adapter over those games
replaces this one in the composition root, and nothing that reads the figure
changes.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from uuid import UUID


class NoGroupBornGames:
    async def born_in(self, group_ids: Collection[UUID]) -> Mapping[UUID, int]:
        return {group_id: 0 for group_id in group_ids}
