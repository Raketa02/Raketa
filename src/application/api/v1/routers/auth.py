from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from application.api.v1.dependencies.auth import get_jwt_service
from application.core.database import get_db
from application.core.security import JwtService, PasswordHasher
from application.domain.auth.schemas import (
    LogoutRequest,
    LogoutResponse,
    RefreshRequest,
    TokenResponse,
)
from application.domain.auth.service import TokenService

router = APIRouter(prefix="/auth", tags=["auth"])


def _password_hasher() -> PasswordHasher:
    return PasswordHasher()


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Rotate refresh and access tokens",
)
async def refresh(
    payload: RefreshRequest,
    db: AsyncSession = Depends(get_db),
    hasher: PasswordHasher = Depends(_password_hasher),
    jwt_service: JwtService = Depends(get_jwt_service),
) -> TokenResponse:
    return await TokenService(db, jwt_service, hasher).refresh(payload.refresh_token)


@router.post(
    "/logout",
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK,
    summary="Revoke a refresh token (idempotent)",
)
async def logout(
    payload: LogoutRequest,
    db: AsyncSession = Depends(get_db),
    hasher: PasswordHasher = Depends(_password_hasher),
    jwt_service: JwtService = Depends(get_jwt_service),
) -> LogoutResponse:
    await TokenService(db, jwt_service, hasher).revoke_refresh(payload.refresh_token)
    return LogoutResponse()
