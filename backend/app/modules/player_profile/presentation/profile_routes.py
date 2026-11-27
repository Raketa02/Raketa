"""The profile commit: one request that ends onboarding's second part.

**One endpoint, one transaction, one profile.** The six social steps are a
client-held draft and nothing is written until the part ends
(``docs/adr/0090``), so this is where all six answers arrive at once — and it
either records every one of them or none.

**The route is ``/players/me/profile``, not ``/users/me/profile``.** The resource
is a *player's* profile: it holds tags, photos, a week and a location,
which are facts about somebody acting in the player app, not about an account.
The identity behind both is the same ``UserId`` (``../../../../CONTEXT.md`` —
*Player*), and the noun is the one the domain uses for what is being described.

**The intro rides on this same commit too**, and is edited afterwards with the
tags and the photos — ``docs/adr/0170`` §5 held the three back until they could
be edited together, and ``docs/adr/0179`` §6 is that day, on the profile
surface next door. **The gender answer rides on this same commit** and its
correction is the surface's too (``docs/adr/0096``): it is required at profile
creation, and profile creation is one request. Which *screen* asks it, and where
that screen sits in onboarding's second part, is ADR-0096's to design and is
not decided here — what is decided here is only that the answer arrives with
the others or the profile is not created.

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
from app.modules.player_profile.domain.intro import INTRO_MAX_CHARACTERS
from app.modules.player_profile.presentation.dependencies import (
    CommitPlayerProfileDep,
)
from app.modules.player_profile.presentation.schemas import (
    CommitPlayerProfileRequest,
    PlayerProfileResponse,
)
from app.modules.users.presentation.dependencies import (
    ADULT_ATTESTATION_MISSING,
    AttestedPlayerDep,
)

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
            "profile, whatever a flaky connection does to the response."
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
                "`weekly_hours_empty` — nothing ticked on the week. At least "
                "one of its 112 hours; the minimum is exactly one and is not "
                "served.\n\n"
                "`too_many_photos` / `duplicate_photo` — the photo list is not "
                "one a profile may hold.\n\n"
                "`intro_not_admitted` — the line is not one the platform "
                "admits, with one coarse `details.reason`: `too_long` (over "
                f"{INTRO_MAX_CHARACTERS} characters after trimming), "
                "`multiline` (a line break), or `contains_contact` (a phone "
                "number, an email, a URL or bare domain, or an `@handle`). "
                "Refused before anything is stored; the client says what to "
                "change and the server never says what it matched.\n\n"
                "`location_club_unknown` — the club picked in place of a "
                "reading is no club in Rakieta (`details.field` `club_id`): it "
                "stopped existing between the search and the tap, or the client "
                "invented it."
            ),
        },
        **ADULT_ATTESTATION_MISSING,
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
        "vocabulary and the tag floor and ceiling are all served by "
        "`GET /player-profile/options` so a client can build controls "
        "that cannot produce an illegal value — and a disabled button is not a "
        "validation. Photo ids are checked to exist *and* to belong to the "
        "caller.\n\n"
        "**`weekly_hours` are required**, at least one hour of the 7 × 16 week "
        "(07:00 to 23:00). Silence about when a player usually plays is never "
        "scored as a zero, so it is asked for rather than guessed at. The "
        "minimum is exactly one and is not served — it is fixed, and a client "
        "holds it as a constant.\n\n"
        "**`location` is a reading or a club, and exactly one.** The phone's "
        "fix (`latitude` and `longitude`), or — for a player who refused the "
        "phone's location — a `club_id` they picked near where they play "
        "(`docs/adr/0200` §10). Either is rounded to the cell before anything "
        "is recorded; a profile cannot exist without one.\n\n"
        "**No search radius and no proposals opt-in.** Both were asked here "
        "and went with the ranking that read them (#581); a body that still "
        "carries either commits, and the two are ignored.\n\n"
        "**`gender` is required and `gender_preference` is not.** The first is "
        "asked once, here, with `PREFER_NOT_TO_SAY` a first-class answer — "
        "there is no unanswered state to send, so a missing or unknown value "
        "is a 422 rather than a coded refusal. The second defaults to `ANY`, "
        "is durable, and gates **both directions**: narrowing it also hides "
        "this player from the side it excludes. Neither value ever comes back "
        "out of this API.\n\n"
        "**`intro` is optional and fenced at the write.** One line about "
        f"yourself, at most {INTRO_MAX_CHARACTERS} characters, any language; "
        "a player who skips sends nothing and has no intro rather than an "
        "empty one. A line carrying a phone number, an email, a URL or an `@handle` is "
        "refused with `intro_not_admitted` before anything is stored. It "
        "crosses on the player card and on the record, and is not echoed here."
    ),
)
async def commit_player_profile(
    payload: CommitPlayerProfileRequest,
    idempotency_key: IdempotencyKeyDep,
    user: AttestedPlayerDep,
    use_case: CommitPlayerProfileDep,
    response: Response,
) -> PlayerProfileResponse:
    committed = await use_case.execute(
        CommitPlayerProfileCommand(
            player_id=user.id,
            idempotency_key=idempotency_key,
            social_tag_ids=payload.social_tag_ids,
            photo_ids=payload.photo_ids,
            weekly_hours=payload.weekly_hours_cells(),
            location=payload.location.as_source(),
            gender=payload.gender,
            gender_preference=payload.gender_preference,
            intro=payload.intro,
        )
    )
    if not committed.created:
        response.status_code = status.HTTP_200_OK
    return PlayerProfileResponse.from_domain(committed.profile)
