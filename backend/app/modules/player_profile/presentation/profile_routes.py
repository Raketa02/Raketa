"""The profile commit: one request that ends onboarding's second part.

**One endpoint, one transaction, one profile.** The six social steps are a
client-held draft and nothing is written until the part ends
(``docs/adr/0090``), so this is where all six answers arrive at once — and it
either records every one of them or none.

**The route is ``/players/me/profile``, not ``/users/me/profile``.** The resource
is a *player's* profile: it holds tags, photos, a week, a location and a consent,
which are facts about somebody acting in the player app, not about an account.
The identity behind both is the same ``UserId`` (``../../../../CONTEXT.md`` —
*Player*), and the noun is the one the domain uses for what is being described.

The `Idempotency-Key` header is required rather than optional, deliberately.
This is the request a player makes once, at the end of six steps, on whatever
connection they have — precisely the control that gets double-tapped and the
response that gets lost. A key the client always sends is a retry that always
costs nothing; a key it sends only when it remembers to is a second profile
waiting for a bad afternoon.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Header, Response, status

from app.core.exception_handlers import ErrorResponse
from app.modules.player_profile.application.commands import (
    CommitPlayerProfileCommand,
)
from app.modules.player_profile.domain.consent import ConsentSurface
from app.modules.player_profile.presentation.dependencies import (
    CommitPlayerProfileDep,
)
from app.modules.player_profile.presentation.schemas import (
    CommitPlayerProfileRequest,
    PlayerProfileResponse,
)
from app.modules.users.presentation.dependencies import CurrentUserDep

router = APIRouter(prefix="/players/me", tags=["player-profile"])

#: The longest idempotency key this endpoint will accept. Generous enough for a
#: uuid, a ulid or a hash, short enough that the header cannot be used to store
#: something in the event stream that is not an identifier of a request.
_MAX_IDEMPOTENCY_KEY_LENGTH = 128

IdempotencyKeyDep = Annotated[
    str,
    Header(
        alias="Idempotency-Key",
        min_length=1,
        max_length=_MAX_IDEMPOTENCY_KEY_LENGTH,
        description=(
            "What the client calls this commit. Sending the same key again "
            "returns the profile the first call created, with a 200 — one "
            "profile, one consent answer, whatever a flaky connection does to "
            "the response."
        ),
    ),
]


@router.post(
    "/profile",
    response_model=PlayerProfileResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_200_OK: {
            "model": PlayerProfileResponse,
            "description": (
                "This idempotency key has already been committed; the profile "
                "the first call created is returned and nothing was recorded."
            ),
        },
        status.HTTP_201_CREATED: {
            "model": PlayerProfileResponse,
            "description": "The profile was created.",
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": (
                "`unknown_social_tag` — an id this platform does not serve; "
                "re-read `GET /player-profile/options`.\n\n"
                "`social_tag_selection_out_of_bounds` — too few or too many "
                "tags for the served floor and ceiling.\n\n"
                "`duplicate_social_tag` — the same tag id arrived twice.\n\n"
                "`search_radius_out_of_bounds` — outside the served range, or "
                "off its step.\n\n"
                "`availability_grid_empty` — nothing ticked on the week. At "
                "least one of the twenty-one cells; the minimum is exactly one "
                "and is not served.\n\n"
                "`proposals_opt_in_not_answered` — the answer was `null`. Ask "
                "the question; do not send `false` on the player's behalf.\n\n"
                "`too_many_photos` / `duplicate_photo` — the photo list is not "
                "one a profile may hold."
            ),
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": (
                "`photo_not_found` — a photo id that does not exist, or belongs "
                "to another player. The two answer the same way deliberately."
            ),
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": (
                "`player_profile_already_exists` — this player has a profile "
                "and this is a **different** idempotency key, so it is a second "
                "commit rather than a retry of the first.\n\n"
                "`concurrent_modification` — two commits for this player raced "
                "and this one lost. Retry: the retry replays the winner."
            ),
        },
    },
    summary="Commit every answer from onboarding's second part",
    description=(
        "Idempotent per `Idempotency-Key`. The same key twice creates one "
        "profile and returns the same body — the second call answers 200 and "
        "records nothing.\n\n"
        "**Every rule the picker enforced is re-validated here.** The tag "
        "vocabulary, the tag floor and ceiling and the radius bounds are all "
        "served by `GET /player-profile/options` so a client can build controls "
        "that cannot produce an illegal value — and a disabled button is not a "
        "validation. Photo ids are checked to exist *and* to belong to the "
        "caller.\n\n"
        "**The availability grid is required**, at least one of its twenty-one "
        "cells. Silence about when a player usually plays is never scored as a "
        "zero, so it is asked for rather than guessed at. The minimum is "
        "exactly one and is not served — it is fixed, and a client holds it as "
        "a constant.\n\n"
        "**The proposals opt-in has no default.** Send the player's actual "
        "answer; `null` is refused rather than treated as a no. The answer is "
        "recorded with the moment, the copy version shown and the surface, "
        "because consent is evidenced rather than asserted."
    ),
)
async def commit_player_profile(
    payload: CommitPlayerProfileRequest,
    idempotency_key: IdempotencyKeyDep,
    user: CurrentUserDep,
    use_case: CommitPlayerProfileDep,
    response: Response,
) -> PlayerProfileResponse:
    committed = await use_case.execute(
        CommitPlayerProfileCommand(
            player_id=user.id,
            idempotency_key=idempotency_key,
            social_tag_ids=payload.social_tag_ids,
            photo_ids=payload.photo_ids,
            availability=payload.availability_cells(),
            latitude=payload.location.latitude,
            longitude=payload.location.longitude,
            search_radius_km=payload.search_radius_km,
            proposals_opt_in=payload.proposals_opt_in.accepted,
            consent_copy_version=payload.proposals_opt_in.copy_version,
            # The surface is this route's own fact, not the client's to declare.
            # This endpoint *is* the end of onboarding's second part, so a body
            # that could name a different surface would be a body that could lie
            # about where a consent was gathered.
            consent_surface=ConsentSurface.ONBOARDING,
        )
    )
    if not committed.created:
        response.status_code = status.HTTP_200_OK
    return PlayerProfileResponse.from_domain(committed.profile)
