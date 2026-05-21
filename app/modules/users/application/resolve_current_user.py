from __future__ import annotations

from uuid import UUID

import jwt

from app.core.exception_handlers import UnauthorizedError
from app.modules.auth.domain.ports import TokenService
from app.modules.users.application.get_current_user import GetCurrentUser
from app.modules.users.domain.user import User


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
        if not raw_token:
            raise UnauthorizedError("missing bearer token")
        

        try:
            payload = self._token_service.decode_access(raw_token)
        except jwt.ExpiredSignatureError as exc:
            raise UnauthorizedError("access token expired") from exc
        except jwt.InvalidTokenError as exc:
            raise UnauthorizedError("invalid access token") from exc

        try:
            user_id = UUID(payload["sub"])
        except (KeyError, ValueError) as exc:
            raise UnauthorizedError("malformed token subject") from exc

        return await self._get_current_user.execute(user_id)
