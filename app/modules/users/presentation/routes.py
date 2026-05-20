from fastapi import APIRouter, Depends, status

from app.modules.users.application.commands import RegisterUserCommand
from app.modules.users.application.register_user import RegisterUser
from app.modules.users.domain.user import User
from app.modules.users.presentation.dependencies import (
    current_user,
    get_register_user,
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
    use_case: RegisterUser = Depends(get_register_user),
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
async def me(user: User = Depends(current_user)) -> UserResponse:
    return UserResponse.from_domain(user)
