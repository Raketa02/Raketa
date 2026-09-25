"""``AccountHolders`` over ``users``' own account operations and the Player
profile's published answer.

Everything written to a User is written by ``users`` — ``InvitationAccounts``
for an account opened or cleared, and the ``PasswordAccounts`` *Forgot
password?* recovers through for a password set; this adapter only translates.
*Acts as a player* is the two providers read together — the attestation off the
User's stream, the Player profile off its own — and is answered here, in this
context's words, because it is this context's question (``docs/adr/0185``
§1–§2).
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from app.kernel import Instant
from app.modules.administrators.domain.ports import AccountHolder
from app.modules.auth.domain.ports import PasswordAccounts
from app.modules.player_profile.application.has_player_profile import (
    HasPlayerProfile,
)
from app.modules.users.application.invitation_accounts import InvitationAccounts
from app.modules.users.domain.value_objects import Email, Name


class UsersAccountHolders:
    def __init__(
        self,
        *,
        accounts: InvitationAccounts,
        passwords: PasswordAccounts,
        profiles: HasPlayerProfile,
    ) -> None:
        self._accounts = accounts
        self._passwords = passwords
        self._profiles = profiles

    async def holder_of(self, email: Email) -> Optional[AccountHolder]:
        found = await self._accounts.holder_of(email)
        if found is None:
            return None
        return AccountHolder(id=found.id, can_sign_in=found.has_password)

    async def open_account(
        self, *, email: Email, name: Name, password_hash: str, at: Instant
    ) -> UUID:
        return await self._accounts.open(
            email=email, name=name, password_hash=password_hash, at=at
        )

    async def set_password(
        self, account_id: UUID, *, password_hash: str, at: Instant
    ) -> None:
        await self._passwords.set_password(
            account_id, password_hash=password_hash, at=at
        )

    async def clear_password(self, account_id: UUID, *, at: Instant) -> None:
        await self._accounts.clear_password(account_id, at=at)

    async def acts_as_player(self, account_id: UUID) -> bool:
        return await self._accounts.adult_attested(
            account_id
        ) or await self._profiles.execute(account_id)
