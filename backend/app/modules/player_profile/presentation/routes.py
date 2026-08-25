"""The Player profile context's read-only endpoints.

One route today: the Social tag vocabulary and the Search radius bounds, served
so that neither the onboarding picker nor the profile editor that will edit the
same values later holds a second copy of either (``docs/adr/0089``). It follows
the precedent ``GET /api/v1/sports`` set for the ``Sport`` registry.

It takes no body, reads nothing per player and needs no token — there is nothing
here that belongs to anybody. That is what makes the answer cacheable, and the
header says so rather than leaving it to a proxy's guess.
"""

from __future__ import annotations

from fastapi import APIRouter, Response, status

from app.modules.player_profile.domain.search_radius import SEARCH_RADIUS_BOUNDS
from app.modules.player_profile.presentation.schemas import (
    PlayerProfileOptionsResponse,
)

router = APIRouter(prefix="/player-profile", tags=["player-profile"])

#: An hour. The vocabulary changes on a release, and a client an hour behind is
#: a client missing a tag nobody has picked yet — ids are permanent, so a stale
#: list is never a *wrong* list.
_CACHE_SECONDS = 3600


@router.get(
    "/options",
    response_model=PlayerProfileOptionsResponse,
    status_code=status.HTTP_200_OK,
    summary="The Social tag vocabulary and the Search radius bounds",
    description=(
        "Read-only, unauthenticated, no request body. Tag **ids** and their "
        "grouping cross the wire; the label a player reads is the client's own "
        "copy.\n\n"
        "A tag id is permanent — it is persisted on profiles, so retiring a tag "
        "means dropping it from this response while continuing to honour it on "
        "the profiles that hold it. Ids are never reused and never renamed.\n\n"
        "Both the group order and the tag order within a group are part of the "
        "contract: the picker renders what it is given rather than sorting."
    ),
)
async def get_player_profile_options(
    response: Response,
) -> PlayerProfileOptionsResponse:
    response.headers["Cache-Control"] = f"public, max-age={_CACHE_SECONDS}"
    return PlayerProfileOptionsResponse.from_domain(SEARCH_RADIUS_BOUNDS)
