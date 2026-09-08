"""``PlayerHandles`` over the port ``users`` already publishes.

**A second copy of ``games``' adapter of the same name, deliberately.** The two
contexts declare the same port and neither may import the other, so the file that
translates *what is this account called* into *what do I print on this seat* is
written once per context. What that buys is that ``users`` may grow a second
reason to answer nothing — an erasure, a suspension — without either context's
wire shape changing, and that neither context is reading the other's port to get
at a third one's.

**It reads the provider's own port and never the provider's table.** A ``select``
over ``UserORM`` written here would make ``challenges`` a second reader of
somebody else's schema, and ``users`` owns both what an account is called and
where that is stored.

**One set read per response, and it is the whole cost of the decision.** A
challenge list of any length asks once, about the union of everybody who holds a
seat on any of its courts.
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
