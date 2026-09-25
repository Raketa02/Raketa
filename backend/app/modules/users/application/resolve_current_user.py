from __future__ import annotations

from dataclasses import dataclass
from typing import final

from app.kernel import Instant
from app.modules.auth.application.access import read_access_token
from app.modules.auth.domain.audience import Audience
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
        the five refusals and one of them getting fixed alone. The refusals
        themselves are ``read_access_token``'s, shared with the club surface, and
        this surface is the **player app's**: a club token is refused here
        (``docs/adr/0185`` §6).
        """

        claims = read_access_token(
            self._token_service, raw_token, audience=Audience.PLAYER_APP
        )
        return AuthenticatedSession(
            user=await self._get_current_user.execute(claims.account_id),
            expires_at=claims.expires_at,
        )
