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

from fastapi import APIRouter, Response, status

from app.core.exception_handlers import ErrorResponse
from app.modules.administrators.presentation.dependencies import (
    ReadAccountProfilesDep,
)
from app.modules.administrators.presentation.schemas import AccountProfilesSchema
from app.modules.player_profile.presentation.dependencies import HasPlayerProfileDep
from app.modules.users.application.attest_adult import AttestAdultCommand
from app.modules.users.application.commands import NameUserCommand, RegisterUserCommand
from app.modules.users.presentation.dependencies import (
    AttestAdultDep,
    CurrentUserDep,
    NameUserDep,
    ReadOwnAccountDep,
    RegisterUserDep,
)
from app.modules.users.presentation.schemas import (
    AdultAttestationRequest,
    MeResponse,
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
    response_model=MeResponse,
    status_code=status.HTTP_200_OK,
    summary="Current authenticated user",
    description=(
        "Carries `name` and `nickname` — the entry gate's first destination is "
        "*not named in full*, either missing — `has_player_profile`, its "
        "fourth, and `adult_attested`, all read from the account's own event "
        "streams rather than from a projection, so a player who has just named "
        "themselves or committed their profile is never sent back to a step "
        "they just finished by a read model that has not caught up. And "
        "`profiles` (docs/adr/0185 §2), which the gate reads **ahead of every "
        "destination**: whether the account acts as a player, the clubs it "
        "administers, and any invitation pending for its email."
    ),
)
async def me(
    user: CurrentUserDep,
    has_profile: HasPlayerProfileDep,
    own: ReadOwnAccountDep,
    profiles: ReadAccountProfilesDep,
) -> MeResponse:
    return MeResponse.from_parts(
        user,
        has_player_profile=await has_profile.execute(user.id),
        own=await own.execute(user.id),
        profiles=AccountProfilesSchema.from_profiles(
            await profiles.execute(account_id=user.id, email=user.email)
        ),
    )


@router.post(
    "/me/adult-attestation",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": (
                "`adult_attestation_required` — the answer was not yes; "
                "`details.field` is `adult_attested`. Nothing was recorded."
            ),
        },
    },
    summary="Attest that you are an adult — Start playing's first step",
    description=(
        "For an account that exists without the Adult attestation: one an "
        "invitation opened, which gives it the first time it acts as a player "
        "(docs/adr/0185 §5). Once given, giving it again records nothing — so "
        "an account that attested at sign-up is answered the same."
    ),
)
async def attest_adult(
    payload: AdultAttestationRequest, user: CurrentUserDep, use_case: AttestAdultDep
) -> Response:
    await use_case.execute(
        AttestAdultCommand(user_id=user.id, adult_attested=payload.adult_attested)
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


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
