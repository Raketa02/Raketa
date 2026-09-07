"""Gate 8's adapter — the account state ``users`` already holds.

The one outward port with a real provider on day one (``docs/adr/0124``). It is a
translation and nothing more: ``users`` publishes *this account is disabled*, and
the matcher's question is *may this candidate be shown*. Keeping the two
sentences apart is what lets ``users`` grow another reason to withhold an account
— an erasure, a suspension — without the gate's name or the matcher's shape
changing.

**It reads the provider's own port and never the provider's table.** The set read
belongs to ``users``, whose repository owns that query; a `select` over `UserORM`
written here would make the matcher a second reader of somebody else's schema.
"""

from __future__ import annotations

from typing import Collection, final
from uuid import UUID

from app.modules.users.domain.ports import UserRepository


@final
class UsersAccountStatus:
    """Withholds exactly the accounts ``users`` reports as disabled."""

    def __init__(self, users: UserRepository) -> None:
        self._users = users

    async def may_not_be_shown(
        self, candidate_ids: Collection[UUID]
    ) -> frozenset[UUID]:
        return await self._users.find_disabled_among(candidate_ids)
