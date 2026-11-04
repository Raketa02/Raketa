"""``PlayerNames`` over the port ``users`` already publishes — the club's one
view of a player on its bookings (#547; the mechanics §16.14: *each player's
name, and whether they paid*).

**The nickname** (``docs/adr/0199`` §5), and nothing else: no photograph, no
Level, no week — what a deck card draws is a player's to be shown by a gate, and
a club's desk passes none. One set read per answer.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from typing import final
from uuid import UUID

from app.modules.users.domain.ports import UserRepository


@final
class UsersPlayerNames:
    def __init__(self, users: UserRepository) -> None:
        self._users = users

    async def names_of(self, player_ids: Collection[UUID]) -> Mapping[UUID, str]:
        if not player_ids:
            return {}
        return await self._users.find_nicknames_of(player_ids)
