from __future__ import annotations

from dataclasses import dataclass

import jwt

from app.kernel import Clock
from app.modules.auth.application.token_rotation import TokenPair, TokenRotator
from app.modules.auth.domain.audience import Audience
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
    SessionHolders,
    TokenService,
)


@dataclass(frozen=True)
class RefreshTokensCommand:
    presented_token: str


class RefreshAuthTokens:
    """Validate the presented refresh token then rotate the pair — **on one
    surface**.

    Built once per audience (``docs/adr/0185`` §6). A refresh token minted for
    the other surface fails the decode as a forgery would, and the stored row is
    asked the same question again, because the row is what records whose the
    token is: a token the JWT and the row disagree about is one this surface did
    not issue. ``holders`` is the audience's own answer to *may this account
    still hold a session*, refused in its own words.
    """

    def __init__(
        self,
        *,
        audience: Audience,
        holders: SessionHolders,
        tokens: RefreshTokenRepository,
        jwt_service: TokenService,
        hasher: PasswordHasher,
        rotator: TokenRotator,
        clock: Clock,
    ) -> None:
        self._audience = audience
        self._holders = holders
        self._tokens = tokens
        self._jwt = jwt_service
        self._hasher = hasher
        self._rotator = rotator
        self._clock = clock

    async def execute(self, command: RefreshTokensCommand) -> TokenPair:
        payload = self._decode(command.presented_token)
        jti = payload["jti"]

        stored = await self._tokens.get_by_jti(jti)
        if stored is None or stored.audience is not self._audience:
            raise RefreshTokenNotRecognised()
        if not stored.is_valid:
            raise RefreshTokenRevoked()
        if not self._hasher.verify(command.presented_token, stored.token_hash):
            raise RefreshTokenMismatch()
        if stored.is_expired(now=self._clock.now()):
            raise RefreshTokenExpired()

        await self._holders.refuse_unless_eligible(stored.account_id)

        return await self._rotator.rotate(stored)

    def _decode(self, token: str) -> dict:
        try:
            return self._jwt.decode_refresh(token, audience=self._audience)
        except jwt.ExpiredSignatureError as exc:
            raise RefreshTokenExpired() from exc
        except jwt.InvalidTokenError as exc:
            raise InvalidRefreshToken() from exc
