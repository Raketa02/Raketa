"""The account endpoints: register, name yourself, and read the authenticated
account back.

``/me`` also carries **whether this player has a Player profile**, which is the
one thing on it that is not the users context's own fact. It is here rather than
on a route of its own because onboarding's entry gate reads it on every cold
launch alongside the account, and two round trips is two things that can fail on
a bad connection (``docs/adr/0090``).

``/me/name`` is **the naming** (``docs/adr/0171`` §2): sign-up asks for
credentials only, and this is the one act that says how people should see a
player — a name and a nickname together, repeatable, refused with the users
context's own conflict when the handle is another player's. It sits beside
``/me`` because that refusal is this context's, and because ``/me`` is where
the gate reads the answer back.

The join is a *use case* from the other context, not a repository reach-in: this
route depends on `HasPlayerProfile`, which depends on that context's port, so
nothing here knows a profile is event-sourced or where its stream lives.
"""

from fastapi import APIRouter, status

from app.core.exception_handlers import ErrorResponse
from app.modules.player_profile.presentation.dependencies import HasPlayerProfileDep
from app.modules.users.application.commands import NameUserCommand, RegisterUserCommand
from app.modules.users.presentation.dependencies import (
    CurrentUserDep,
    NameUserDep,
    ReadNamingDep,
    RegisterUserDep,
)
from app.modules.users.presentation.schemas import (
    NameRequest,
    NamingResponse,
    UserCreateRequest,
    UserResponse,
)

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
            password=payload.password1,
            adult_attested=payload.adult_attested,
        )
    )
    return UserResponse.from_domain(user)


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Current authenticated user",
    description=(
        "Carries `name` and `nickname` — null until the naming, and `name` is the "
        "**first** branch of onboarding's entry gate — and `has_player_profile`, "
        "its fourth. All three are read from the player's own event streams "
        "rather than from a projection, so a player who has just named "
        "themselves or committed their profile is never sent back to a step they "
        "just finished by a read model that has not caught up."
    ),
)
async def me(
    user: CurrentUserDep,
    has_profile: HasPlayerProfileDep,
    naming: ReadNamingDep,
) -> UserResponse:
    return UserResponse.from_domain(
        user,
        has_player_profile=await has_profile.execute(user.id),
        naming=await naming.execute(user.id),
    )


@router.put(
    "/me/name",
    response_model=NamingResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": (
                "`nickname_already_taken` — the handle is another player's, "
                "`details.field` is `nickname`, and nothing was recorded: the "
                "act is one event, so the name is not kept either. The client "
                "writes the sentence under the field."
            ),
        },
    },
    summary="Name yourself — how should people see you?",
    description=(
        "**The naming**: one act carrying a name and a nickname, for the "
        "authenticated player, and repeatable — a later change is the same act, "
        "and keeping the nickname you already hold is admitted. Refused with "
        "`409 nickname_already_taken` when the handle is another player's; the "
        "name is checked against nobody. Answers the pair as recorded — the name "
        "trimmed and collapsed — and the client re-reads `GET /me` before moving "
        "on, which is where the entry gate reads it."
    ),
)
async def name_me(
    payload: NameRequest,
    user: CurrentUserDep,
    use_case: NameUserDep,
) -> NamingResponse:
    naming = await use_case.execute(
        NameUserCommand(
            user_id=user.id, name=payload.name, nickname=payload.nickname
        )
    )
    return NamingResponse(name=naming.name, nickname=naming.nickname)
