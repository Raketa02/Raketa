"""The profile surface Play reads and writes: one read, one `PUT` per fact.

The search screen edits three facts — the availability grid, the search radius
and the per-sport Play intent — and until these routes existed it could read none
of them and write none of them. The engine has been raising `KEEP_THESE_TIMES`
and `KEEP_THIS_RADIUS` the whole time, and `matchmaking/domain/prompts.py` names
the gap in writing: *every one of these questions is answered by a write this
backend has no route for.* This is that write, and the third one is ADR-0094's
`PUT /api/v1/play-intents/{sport}`, next door.

**One `PUT` per fact, unkeyed, and deliberately not a `PATCH`.** Three arguments
converge and the third is decisive:

1. **The shape is already fixed** for the third changeable fact in this same
   context — ADR-0094's unkeyed `PUT`, where *"the resource is one player's
   intent in one sport, the same request twice lands the same state, and the
   no-op rule means the second appends nothing."* Two write shapes in one context
   is the thing worth avoiding.
2. **Each prompt is answered by exactly one write.** `KEEP_THESE_TIMES` writes
   the grid; `KEEP_THIS_RADIUS` writes the radius. A partial update would exist
   to serve a caller that does not exist.
3. **`null` versus absent is fatal on the grid specifically.** A blank grid is a
   **legal value** — `change_availability` accepts one deliberately — so
   `PATCH {"availability": null}` would mean both *leave my week alone* and
   *clear my week*, and the second is a real thing a player does. This is not a
   general dislike of `PATCH`; it is that this field has a legal empty value and
   the ambiguity therefore bites.

**No `Idempotency-Key`.** `profile_routes.py` argues one for the **creating**
commit — *"the request a player makes once, at the end of six steps, on whatever
connection they have"* — and a `PUT` that lands the same state twice has nothing
to deduplicate.

**Read, availability and radius, and nothing else.** The aggregate also has
`change_social_tags`, `change_photos`, `change_location`, `change_gender` and
`change_gender_preference`, and none of them gets a route here. Those belong to
*You*, which is not built; this surface is scoped to what the Play screens edit,
and the read grows the deferred fields when that screen arrives rather than
acquiring a sibling.
"""

from __future__ import annotations

from fastapi import APIRouter, status

from app.core.exception_handlers import ErrorResponse
from app.modules.player_profile.application.commands import (
    ChangeAvailabilityCommand,
    ChangeSearchRadiusCommand,
)
from app.modules.player_profile.presentation.dependencies import (
    ChangeAvailabilityDep,
    ChangeSearchRadiusDep,
    ReadPlayerProfileDep,
)
from app.modules.player_profile.presentation.schemas import (
    AvailabilityResponse,
    ChangeAvailabilityRequest,
    ChangeSearchRadiusRequest,
    PlayerProfileReadResponse,
    SearchRadiusResponse,
)
from app.modules.users.presentation.dependencies import CurrentUserDep

router = APIRouter(prefix="/players/me", tags=["player-profile"])

_NO_PROFILE = {
    "model": ErrorResponse,
    "description": (
        "`player_profile_not_found` — this player has not finished onboarding's "
        "second part. The recovery is that part, which `GET /users/me` already "
        "sends a cold launch into."
    ),
}

#: Both writes append to the profile's stream, so both can lose a version race —
#: the same 409 the creating commit documents, on the same aggregate. Stated here
#: rather than left to be discovered, because a status a route can return and the
#: contract does not list is a branch no generated client has.
_LOST_THE_RACE = {
    "model": ErrorResponse,
    "description": (
        "`concurrent_modification` — two writes reached this player's profile "
        "and this one lost. Retry: the retry reads the winner, and lands the "
        "same state or nothing."
    ),
}


@router.get(
    "/profile",
    response_model=PlayerProfileReadResponse,
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_404_NOT_FOUND: _NO_PROFILE},
    summary="The week, the radius and the Play intent this player declared",
    description=(
        "One read for the three facts the Play screens hold, across the two "
        "aggregates that own them. The fourth fact a search screen needs — "
        "**which sports am I rated in** — is `GET /api/v1/ratings` and is not "
        "re-served here.\n\n"
        "**`play_intents` holds only what was declared.** An undeclared sport is "
        "absent, never `null`: `NO_PREFERENCE` is an explicit answer, so there "
        "is no unanswered value to send. *Rated but undeclared* is a set "
        "difference against `GET /ratings`, and it is what a client uses to open "
        "the declaration interstitial **before** a search is refused with "
        "`play_intent_not_declared` rather than after.\n\n"
        "**An empty `availability` is a real answer.** A player may clear their "
        "week; it means *we do not know when they play* and never *never*.\n\n"
        "## What this response does not carry\n\n"
        "**`gender` and `gender_preference` are withheld and always will be.** "
        "Neither value ever comes back out of this API — the profile commit says "
        "so, and this route does not weaken it.\n\n"
        "**Social tags, photos and location are not served *yet*.** They are "
        "deferred rather than refused, and this is the route that grows them "
        "when the *You* screen is built — there will be no second endpoint for "
        "them. The one to be careful with is **photos**: a profile may legally "
        "hold none, so an absent photo list here must not be read as *this "
        "player has no photographs*. Tags and a location are required at commit, "
        "so their absence cannot be mistaken for an answer either way."
    ),
)
async def read_player_profile(
    user: CurrentUserDep,
    use_case: ReadPlayerProfileDep,
) -> PlayerProfileReadResponse:
    return PlayerProfileReadResponse.from_domain(await use_case.execute(user.id))


@router.put(
    "/availability",
    response_model=AvailabilityResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: _NO_PROFILE,
        status.HTTP_409_CONFLICT: _LOST_THE_RACE,
    },
    summary="Replace this player's week",
    description=(
        "The whole week, every time — the list **is** the grid, and what is "
        "absent from it is unticked. Unkeyed and safe to send twice: the same "
        "week twice lands the same state, and a transition that changes nothing "
        "records nothing.\n\n"
        "**An empty list is a legal value and clears the week.** The floor of "
        "one ticked cell binds the *commit*, which is the answer a player is "
        "asked for at the end of onboarding, and not every later edit of it. A "
        "cleared week is read as *absent* by the matcher, never as a zero — "
        "silence is never scored (`docs/adr/0102`).\n\n"
        "**This is where a `KEEP_THESE_TIMES` prompt is answered.** The engine "
        "notices that a search ran on a week the profile does not hold and asks; "
        "nothing in the matcher writes a profile, so a *yes* is this request. "
        "Declining writes nothing anywhere.\n\n"
        "Repeated cells are collapsed and the response carries the grid as "
        "stored, in the platform's reading order — so a client can see what the "
        "profile now holds rather than assuming it kept what was sent."
    ),
)
async def change_availability(
    payload: ChangeAvailabilityRequest,
    user: CurrentUserDep,
    use_case: ChangeAvailabilityDep,
) -> AvailabilityResponse:
    profile = await use_case.execute(
        ChangeAvailabilityCommand(
            player_id=user.id,
            availability=payload.availability_cells(),
        )
    )
    return AvailabilityResponse.from_domain(profile)


@router.put(
    "/search-radius",
    response_model=SearchRadiusResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": (
                "`search_radius_out_of_bounds` — outside the range served by "
                "`GET /player-profile/options`, or off its step. Re-checked here "
                "even though a slider built from those numbers cannot produce "
                "one: a control is not a validation."
            ),
        },
        status.HTTP_404_NOT_FOUND: _NO_PROFILE,
        status.HTTP_409_CONFLICT: _LOST_THE_RACE,
    },
    summary="Replace this player's Search radius",
    description=(
        "Whole kilometres, unkeyed, and idempotent for the reason the week "
        "is.\n\n"
        "**This is where a `KEEP_THIS_RADIUS` prompt is answered**, and where "
        "taking a relaxation rung becomes durable. A rung is *"
        '"an ask and never a correction"* — running a wider search writes '
        "nothing — and this is the request the offer to keep it turns into. "
        "Accepting is also what stops the prompt: a profile that holds the wider "
        "radius takes no rung on the next search, so the condition that raised "
        "the question is gone rather than suppressed."
    ),
)
async def change_search_radius(
    payload: ChangeSearchRadiusRequest,
    user: CurrentUserDep,
    use_case: ChangeSearchRadiusDep,
) -> SearchRadiusResponse:
    profile = await use_case.execute(
        ChangeSearchRadiusCommand(
            player_id=user.id,
            search_radius_km=payload.search_radius_km,
        )
    )
    return SearchRadiusResponse.from_domain(profile)
