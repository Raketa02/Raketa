from fastapi import APIRouter, status

from app.modules.users.application.commands import RegisterUserCommand
from app.modules.users.presentation.dependencies import (
    CurrentUserDep,
    RegisterUserDep,
)
from app.modules.users.presentation.schemas import UserCreateRequest, UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a user",
)
async def register_user(
    payload: UserCreateRequest,
    use_case: RegisterUserDep,
) -> UserResponse:
    user = await use_case.execute(
        RegisterUserCommand(
            email=payload.email,
            nickname=payload.nickname,
            password=payload.password1,
        )
    )
    return UserResponse.from_domain(user)


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Current authenticated user",
)
async def me(user: CurrentUserDep) -> UserResponse:
    return UserResponse.from_domain(user)
