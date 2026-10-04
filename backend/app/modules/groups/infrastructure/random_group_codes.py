"""``GroupCodeMinter``: eight random characters no group has yet.

**``secrets``, never ``random``**: a group link is a permanent capability — anyone
holding it can find the group and, under *Anyone*, join it (``docs/adr/0183``,
*Harder*) — so its code must not be guessable from the codes around it.

**Checked against the table before it is used, and the unique index is the
guard behind that check.** At 31⁸ codes a collision is a one-in-billions event,
so a handful of draws is enough and running out of them means something other
than bad luck is wrong.
"""

from __future__ import annotations

import secrets
from typing import Final

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.groups.domain.value_objects import (
    GROUP_CODE_ALPHABET,
    GROUP_CODE_LENGTH,
    GroupCode,
)
from app.modules.groups.infrastructure.group_model import GroupORM

_DRAWS: Final = 8


class RandomGroupCodes:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def mint(self) -> GroupCode:
        for _ in range(_DRAWS):
            code = "".join(
                secrets.choice(GROUP_CODE_ALPHABET) for _ in range(GROUP_CODE_LENGTH)
            )
            taken = await self._session.scalar(
                select(GroupORM.id).where(GroupORM.code == code)
            )
            if taken is None:
                return GroupCode(code)
        raise RuntimeError(f"no free group code in {_DRAWS} draws")
