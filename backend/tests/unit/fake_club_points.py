"""``ClubPoints`` for unit tests: the clubs a test placed, and nobody else.

Hand-written against the ``Protocol``, as every port stub here is
(``tests/unit/test_resolve_current_user.py``). A club absent from the map is a
club that is not in Raketa — the one answer ``DirectoryClubPoints`` gives for an
id the directory does not list, which ``tests/demands/`` holds it to.
"""

from __future__ import annotations

from collections.abc import Mapping
from uuid import UUID

from app.modules.player_profile.domain.ports import ClubPoint


class InMemoryClubPoints:
    def __init__(self, points: Mapping[UUID, ClubPoint] | None = None) -> None:
        self.points = dict(points or {})
        self.asked: list[UUID] = []

    async def point_of(self, club_id: UUID) -> ClubPoint | None:
        self.asked.append(club_id)
        return self.points.get(club_id)
