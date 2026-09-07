"""``PlayerHandles`` over the port ``users`` already publishes.

A translation and nothing more, on ``UsersAccountStatus``'s precedent: ``users``
answers *what is this account called*, and this context's question is *what do I
print on this seat*. Keeping the two sentences apart is what lets ``users`` grow
a second reason to answer nothing — an erasure, a suspension — without a game's
wire shape changing.

**It reads the provider's own port and never the provider's table.** A ``select``
over ``UserORM`` written here would make ``games`` a second reader of somebody
else's schema, and ``users`` owns both what an account is called and where that
is stored.

**One set read per response, and it is the whole cost of the decision.** A games
list of any length asks once, about the union of everybody who sat on any of its
courts.
"""

from __future__ import annotations

from typing import Collection, Mapping, final
from uuid import UUID

from app.modules.users.domain.ports import UserRepository


@final
class UsersHandles:
    """What ``users`` calls each of these accounts."""

    def __init__(self, users: UserRepository) -> None:
        self._users = users

    async def handles_of(self, player_ids: Collection[UUID]) -> Mapping[UUID, str]:
        if not player_ids:
            return {}
        return await self._users.find_nicknames_of(player_ids)
