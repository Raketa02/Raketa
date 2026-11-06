"""``FriendLinkCodes`` over ``friend_link_codes``: a random code **no link ever
carried**, and whose link a code is now.

**``secrets``, never ``random``**, as for a group's code: a link must not be
guessable from the codes around it, or from its owner's nickname. **Checked
against every row, current or replaced**, so a code is never reused; the primary
key is the guard behind the check. At 31⁸ codes a collision is a one-in-billions
event, so a handful of draws is enough, and running out of them means something
other than bad luck is wrong.
"""

from __future__ import annotations

import secrets
from typing import Final
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.friends.domain.link import (
    FRIEND_LINK_CODE_ALPHABET,
    FRIEND_LINK_CODE_LENGTH,
    FriendLinkCode,
)
from app.modules.friends.infrastructure.friend_link_model import FriendLinkCodeORM

_DRAWS: Final = 8


class RandomFriendLinkCodes:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def mint(self) -> FriendLinkCode:
        for _ in range(_DRAWS):
            code = "".join(
                secrets.choice(FRIEND_LINK_CODE_ALPHABET)
                for _ in range(FRIEND_LINK_CODE_LENGTH)
            )
            taken = await self._session.scalar(
                select(FriendLinkCodeORM.code).where(FriendLinkCodeORM.code == code)
            )
            if taken is None:
                return FriendLinkCode(code)
        raise RuntimeError(f"no free friend link code in {_DRAWS} draws")

    async def owner_of(self, code: FriendLinkCode) -> UUID | None:
        return await self._session.scalar(
            select(FriendLinkCodeORM.owner_id).where(
                FriendLinkCodeORM.code == code.value, FriendLinkCodeORM.current
            )
        )
