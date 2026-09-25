from __future__ import annotations

from uuid import UUID

from app.modules.users.application.get_current_user import GetCurrentUser
from app.modules.users.domain.ports import UserRepository


class UserSessionHolders:
    """``SessionHolders`` for the player app: a session is a User's, and only an
    active one may refresh it.

    **The rule is ``GetCurrentUser``'s, asked through it** — the one every
    request applies — so a disabled account can neither use nor renew a session,
    and the refusal is the ``user_not_eligible`` the player app has always been
    told on this path.
    """

    def __init__(self, users: UserRepository) -> None:
        self._current_user = GetCurrentUser(users)

    async def refuse_unless_eligible(self, account_id: UUID) -> None:
        await self._current_user.execute(account_id)
