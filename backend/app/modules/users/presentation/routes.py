"""The account endpoints: register, and read the authenticated one back.

``/me`` also carries **whether this player has a Player profile**, which is the
one thing on it that is not the users context's own fact. It is here rather than
on a route of its own because onboarding's entry gate reads it on every cold
launch alongside the account, and two round trips is two things that can fail on
a bad connection (``docs/adr/0090``).

The join is a *use case* from the other context, not a repository reach-in: this
route depends on `HasPlayerProfile`, which depends on that context's port, so
nothing here knows a profile is event-sourced or where its stream lives.
"""

from fastapi import APIRouter, status

from app.modules.player_profile.presentation.dependencies import HasPlayerProfileDep
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
    # `has_player_profile` is left at its default here, and false is the honest
    # answer: an account that was created one line ago cannot have committed a
    # profile. Nothing is asked of the other context to establish that.
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
    description=(
        "Carries `has_player_profile`, the fourth branch of onboarding's entry "
        "gate. It is read from the profile's event stream rather than from a "
        "projection, so a player who has just committed their profile is never "
        "sent back into the social steps by a read model that has not caught up."
    ),
)
async def me(user: CurrentUserDep, has_profile: HasPlayerProfileDep) -> UserResponse:
    return UserResponse.from_domain(
        user, has_player_profile=await has_profile.execute(user.id)
    )
