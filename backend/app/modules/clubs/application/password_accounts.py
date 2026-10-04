"""``PasswordAccounts`` for the club website: a recoverable password is a Club
account's.

Answered here, beside ``ClubAccountSessionHolders``, because a club's sign-in is
this context's aggregate (``docs/adr/0182`` §3) and the change is an event on
its own stream (``docs/adr/0185`` §7), projected onto the row every club
request reads. The lookup is among Club accounts only: the same address may be
an unrelated player's, whose password this never touches.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from app.kernel import Instant
from app.modules.auth.domain.ports import PasswordAccount
from app.modules.clubs.domain.ports import ClubAccountRepository
from app.modules.users.domain.value_objects import Email, HashedPassword


class ClubPasswordAccounts:
    def __init__(self, accounts: ClubAccountRepository) -> None:
        self._accounts = accounts

    async def recoverable(self, email: str) -> Optional[PasswordAccount]:
        # Nothing disables a Club account yet, so *may still sign in* is
        # *exists* — the rule ``eligible_club_account`` states for a session.
        account = await self._accounts.get_by_email(Email(email))
        if account is None:
            return None
        return PasswordAccount(id=account.id, email=account.email.value)

    async def set_password(
        self, account_id: UUID, *, password_hash: str, at: Instant
    ) -> None:
        account = await self._accounts.load(account_id)
        if account is None:
            raise RuntimeError(
                f"club account {account_id} has no stream to set a password on"
            )
        account.change_password(
            password_hash=HashedPassword(password_hash), occurred_at=at
        )
        await self._accounts.save(account)
