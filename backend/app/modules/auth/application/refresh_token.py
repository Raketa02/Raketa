from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

import jwt

from app.kernel import Clock
from app.modules.auth.application.token_rotation import TokenPair, TokenRotator
from app.modules.auth.domain.errors import (
    InvalidRefreshToken,
    RefreshTokenExpired,
    RefreshTokenMismatch,
    RefreshTokenNotRecognised,
    RefreshTokenRevoked,
)
from app.modules.auth.domain.ports import (
    PasswordHasher,
    RefreshTokenRepository,
    TokenService,
)
from app.modules.users.domain.errors import UserNotEligible
from app.modules.users.domain.ports import UserRepository


@dataclass(frozen=True)
class RefreshTokensCommand:
    presented_token: str


class RefreshAuthTokens:
    """Validate the presented refresh token then rotate the pair."""

    def __init__(
        self,
        users: UserRepository,
        tokens: RefreshTokenRepository,
        jwt_service: TokenService,
        hasher: PasswordHasher,
        rotator: TokenRotator,
        clock: Clock,
    ) -> None:
        self._users = users
        self._tokens = tokens
        self._jwt = jwt_service
        self._hasher = hasher
        self._rotator = rotator
        self._clock = clock

    async def execute(self, command: RefreshTokensCommand) -> TokenPair:
        payload = self._decode(command.presented_token)
        user_id = UUID(payload["sub"])
        jti = payload["jti"]

        stored = await self._tokens.get_by_jti(jti)
        if stored is None:
            raise RefreshTokenNotRecognised()
        if not stored.is_valid:
            raise RefreshTokenRevoked()
        if not self._hasher.verify(command.presented_token, stored.token_hash):
            raise RefreshTokenMismatch()
        if stored.is_expired(now=self._clock.now()):
            raise RefreshTokenExpired()

        user = await self._users.get_by_id(user_id)
        if user is None or not user.is_active:
            raise UserNotEligible()

        return await self._rotator.rotate(stored, user_id)

    def _decode(self, token: str) -> dict:
        try:
            return self._jwt.decode_refresh(token)
        except jwt.ExpiredSignatureError as exc:
            raise RefreshTokenExpired() from exc
        except jwt.InvalidTokenError as exc:
            raise InvalidRefreshToken() from exc
