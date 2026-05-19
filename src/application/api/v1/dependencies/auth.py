from uuid import UUID

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from application.core.config import Settings, get_settings
from application.core.database import get_db
from application.core.exceptions import UnauthorizedError
from application.core.security import JwtService
from application.domain.user.entities import User
from application.domain.user.repository import UserRepository

_bearer = HTTPBearer(auto_error=False, description="Bearer access token")


def get_jwt_service(settings: Settings = Depends(get_settings)) -> JwtService:
    return JwtService(settings)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
    jwt_service: JwtService = Depends(get_jwt_service),
) -> User:
    if credentials is None or not credentials.credentials:
        raise UnauthorizedError("missing bearer token")
    try:
        payload = jwt_service.decode(credentials.credentials, JwtService.ACCESS)
    except jwt.ExpiredSignatureError as exc:
        raise UnauthorizedError("access token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise UnauthorizedError("invalid access token") from exc

    try:
        user_id = UUID(payload["sub"])
    except (KeyError, ValueError) as exc:
        raise UnauthorizedError("malformed token subject") from exc

    user = await UserRepository(db).get_by_id(user_id)
    if user is None or not user.is_active:
        raise UnauthorizedError("user no longer eligible")
    return user
