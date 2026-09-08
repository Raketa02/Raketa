from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import final
from uuid import UUID

import jwt

from app.kernel import Instant, instant
from app.modules.auth.domain.errors import (
    AccessTokenExpired,
    AccessTokenInvalid,
    AccessTokenMissing,
    AccessTokenSubjectMalformed,
)
from app.modules.auth.domain.ports import TokenService
from app.modules.users.application.get_current_user import GetCurrentUser
from app.modules.users.domain.user import User


@final
@dataclass(frozen=True, slots=True)
class AuthenticatedSession:
    """Who is calling, **and when their permission to be here runs out.**

    The second half exists for one caller and it is the live channel: a stream is
    closed at the access token's ``exp`` rather than allowed to outlive it
    (``docs/adr/0147`` §6), because a connection authenticated once and left open
    hands a revoked player up to an hour of live delivery — against
    ``docs/adr/0004``, whose whole point is prompt revocation.

    **It is read off the token rather than recomputed from a TTL.** The two agree
    today; they would part company the day the setting changed, and the honest
    deadline is the one written into the credential the caller actually presented.
    """

    user: User
    expires_at: Instant


class ResolveCurrentUserFromAccessToken:
    """Translate a raw bearer token into the active domain user it represents."""

    def __init__(
        self,
        token_service: TokenService,
        get_current_user: GetCurrentUser,
    ) -> None:
        self._token_service = token_service
        self._get_current_user = get_current_user

    async def execute(self, raw_token: str | None) -> User:
        """Who is calling. **The answer every ordinary route wants.**"""

        return (await self.authenticated_session(raw_token)).user

    async def authenticated_session(
        self, raw_token: str | None
    ) -> AuthenticatedSession:
        """Who is calling, and until when.

        **One decode, in one place.** The alternative was a second dependency
        that decoded the same token again for its ``exp``, which is two copies of
        the five refusals below and one of them getting fixed alone.
        """

        if not raw_token:
            raise AccessTokenMissing()

        try:
            payload = self._token_service.decode_access(raw_token)
        except jwt.ExpiredSignatureError as exc:
            raise AccessTokenExpired() from exc
        except jwt.InvalidTokenError as exc:
            raise AccessTokenInvalid() from exc

        try:
            user_id = UUID(payload["sub"])
        except (KeyError, ValueError) as exc:
            raise AccessTokenSubjectMalformed() from exc

        try:
            expires_at = instant(
                datetime.fromtimestamp(int(payload["exp"]), tz=timezone.utc)
            )
        except (KeyError, TypeError, ValueError, OverflowError, OSError) as exc:
            # **The fifth refusal, and it is not defensive.** An access token
            # with no readable expiry is one nothing can close a live stream on
            # (``docs/adr/0147`` §6), and a credential that never runs out is
            # exactly what ``docs/adr/0004`` refuses. ``JwtTokenService`` already
            # requires ``exp`` on decode, so this is the port's contract stated
            # where the port is consumed rather than trusted to every adapter.
            raise AccessTokenInvalid() from exc

        return AuthenticatedSession(
            user=await self._get_current_user.execute(user_id),
            expires_at=expires_at,
        )
