from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from application.api.v1.dependencies.auth import get_current_user, get_jwt_service
from application.core.database import get_db
from application.core.security import JwtService, PasswordHasher
from application.domain.auth.schemas import TokenResponse
from application.domain.auth.service import TokenService
from application.domain.user.entities import User
from application.domain.user.schemas import (
    LoginRequest,
    UserCreateRequest,
    UserResponse,
)
from application.domain.user.service import UserService

router = APIRouter(prefix="/api/v1/users", tags=["users"])


def _password_hasher() -> PasswordHasher:
    return PasswordHasher()


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a user",
)
async def create_user(
    payload: UserCreateRequest,
    db: AsyncSession = Depends(get_db),
    hasher: PasswordHasher = Depends(_password_hasher),
) -> UserResponse:
    user = await UserService(db, hasher).create_user(payload)
    return UserResponse.from_orm(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Login and obtain an access/refresh token pair",
)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
    hasher: PasswordHasher = Depends(_password_hasher),
    jwt_service: JwtService = Depends(get_jwt_service),
) -> TokenResponse:
    user = await UserService(db, hasher).authenticate(payload)
    tokens = TokenService(db, jwt_service, hasher)
    return await tokens.issue_token_pair(user.id)


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Current authenticated user",
)
async def me(current: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.from_orm(current)
