from __future__ import annotations

from dataclasses import dataclass

from app.modules.auth.application.token_rotation import TokenPair, TokenRotator
from app.modules.auth.domain.errors import AccountDisabled, InvalidCredentials
from app.modules.auth.domain.ports import PasswordHasher
from app.modules.users.domain.ports import UserRepository


@dataclass(frozen=True)
class LoginCommand:
    email: str
    password: str


class Login:
    """Verify email + password and issue a fresh token pair."""

    def __init__(
        self,
        users: UserRepository,
        hasher: PasswordHasher,
        rotator: TokenRotator,
    ) -> None:
        self._users = users
        self._hasher = hasher
        self._rotator = rotator

    async def execute(self, command: LoginCommand) -> TokenPair:
        user = await self._users.get_by_email(command.email.strip().lower())
        if user is None or not self._hasher.verify(
            command.password, user.password_hash.value
        ):
            raise InvalidCredentials()
        if not user.is_active:
            raise AccountDisabled()
        return await self._rotator.issue_pair(user.id)
