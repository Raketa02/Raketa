from datetime import datetime, timezone
from typing import Tuple
from uuid import UUID

import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from application.core.exceptions import UnauthorizedError
from application.core.security import JwtService, PasswordHasher
from application.domain.auth.entities import RefreshToken
from application.domain.auth.repository import RefreshTokenRepository
from application.domain.auth.schemas import TokenResponse
from application.domain.user.entities import User
from application.domain.user.repository import UserRepository


class TokenService:
    """Issues / refreshes / revokes JWT pairs and persists refresh-token state."""

    def __init__(
        self,
        session: AsyncSession,
        jwt_service: JwtService,
        password_hasher: PasswordHasher,
    ) -> None:
        self._session = session
        self._jwt = jwt_service
        self._hasher = password_hasher
        self._tokens = RefreshTokenRepository(session)
        self._users = UserRepository(session)

    async def issue_token_pair(self, user_id: UUID) -> TokenResponse:
        access = self._jwt.issue_access(str(user_id))
        refresh = self._jwt.issue_refresh(str(user_id))

        row = RefreshToken(
            user_id=user_id,
            token_hash=self._hasher.hash(refresh.token),
            jti=refresh.jti,
            refresh_expires_at=refresh.expires_at,
            is_valid=True,
        )
        await self._tokens.add(row)
        await self._session.commit()

        return TokenResponse(
            access_token=access.token,
            refresh_token=refresh.token,
            token_type="bearer",
            expires_in=self._jwt.access_ttl_seconds,
        )

    async def refresh(self, presented_token: str) -> TokenResponse:
        payload = self._decode_refresh_or_raise(presented_token)
        user_id = UUID(payload["sub"])
        jti = payload["jti"]

        stored = await self._tokens.get_by_jti(jti)
        if stored is None:
            raise UnauthorizedError("refresh token not recognised")
        if not stored.is_valid:
            raise UnauthorizedError("refresh token has been revoked")
        if not self._hasher.verify(presented_token, stored.token_hash):
            raise UnauthorizedError("refresh token does not match")

        # The JWT lib already enforces exp; this guard handles clock skew + safety.
        # SQLite returns naive datetimes — treat them as UTC so the comparison works
        # against both Postgres (tz-aware) and SQLite (naive).
        stored_exp = stored.refresh_expires_at
        if stored_exp.tzinfo is None:
            stored_exp = stored_exp.replace(tzinfo=timezone.utc)
        if stored_exp <= datetime.now(timezone.utc):
            raise UnauthorizedError("refresh token expired")

        user = await self._users.get_by_id(user_id)
        if user is None or not user.is_active:
            raise UnauthorizedError("user no longer eligible")

        # Rotation: invalidate the presented refresh, issue a new pair.
        await self._tokens.revoke(stored, now=datetime.now(timezone.utc))
        return await self.issue_token_pair(user_id)

    async def revoke_refresh(self, presented_token: str) -> None:
        """Idempotent: revokes if recognised, silently no-ops otherwise.

        We deliberately do not signal whether the token was found — logout must
        not leak token existence."""
        try:
            payload = self._decode_refresh_or_raise(presented_token)
        except UnauthorizedError:
            return
        stored = await self._tokens.get_by_jti(payload["jti"])
        if stored is None or not stored.is_valid:
            return
        if not self._hasher.verify(presented_token, stored.token_hash):
            return
        await self._tokens.revoke(stored, now=datetime.now(timezone.utc))
        await self._session.commit()

    # ----- internals

    def _decode_refresh_or_raise(self, token: str) -> dict:
        try:
            return self._jwt.decode(token, JwtService.REFRESH)
        except jwt.ExpiredSignatureError as exc:
            raise UnauthorizedError("refresh token expired") from exc
        except jwt.InvalidTokenError as exc:
            raise UnauthorizedError("invalid refresh token") from exc


def login_user(
    user: User,
    session: AsyncSession,
    jwt_service: JwtService,
    password_hasher: PasswordHasher,
) -> Tuple[TokenService, UUID]:
    """Tiny factory wrapper so route handlers don't construct services directly."""
    return TokenService(session, jwt_service, password_hasher), user.id
