"""*Find me a game* — one route, and it is deliberately not idempotent.

**Two taps are two searches.** The index moved between them, and the product's
own denominator is *searches run*: collapsing a double tap would put a lie in the
one table the product uses to judge itself. There is no idempotency window and no
``Idempotency-Key``.

This is the opposite of the assessments router's idiom — a `POST` returning the
run you are already in — and the difference is the point: an assessment is a
thing you are in the middle of, a search is a thing that happened.

**The client sends asks, never facts.** The body carries a sport and a mode. The
profile, the grid, the radius, the tags, the rating, the intent and the gender
preference are read by the backend at request time, because a stale radius from a
phone is a gate evaluated on a lie.

**An empty shortlist is a `200`** with the pool described. The honest empty state
is an answer, not a failure — and it is recorded exactly like any other search.

**Never a fallback list.** Every failure below is a refusal with a distinct code.
When the engine is down the feature is down; a hand-rolled backend ranker
arriving as a hotfix is how a second, worse, unexplainable ranking implementation
enters the system permanently.
"""

from __future__ import annotations

from fastapi import APIRouter, Request, status

from app.core.exception_handlers import ErrorResponse
from app.core.tracing import trace_id_for
from app.modules.matchmaking.application.commands import RunShortlistSearchCommand
from app.modules.matchmaking.presentation.dependencies import RunShortlistSearchDep
from app.modules.matchmaking.presentation.rendering import render
from app.modules.matchmaking.presentation.schemas import (
    RunSearchRequest,
    ShortlistResponse,
)
from app.modules.users.presentation.dependencies import CurrentUserDep

router = APIRouter(prefix="/searches", tags=["searches"])


@router.post(
    "",
    response_model=ShortlistResponse,
    # Every **omitted** field is omitted because this module never set it, which
    # is `docs/adr/0106` §4's first spelling made literal: `field?: T` on the
    # generated client, and genuinely absent from the JSON. A field set to
    # `None` is the second spelling and still crosses — a measured nothing.
    response_model_exclude_unset=True,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": (
                "A ranked shortlist of at most twenty, each row carrying a Fit "
                "out of a hundred and the complete breakdown that produced it. "
                "**An empty list is also a 200** — the honest empty state is an "
                "answer, and the pool it came from is described either way."
            ),
        },
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorResponse,
            "description": "`account_held` — this account is under a live hold.",
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": (
                "`sport_not_rated` — you hold no rating for this sport.\n\n"
                "`play_intent_not_declared` — you have not said what kind of "
                "evening you are after for it.\n\n"
                "`player_profile_not_committed` — there is no profile to read a "
                "radius, a grid or an area from."
            ),
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ErrorResponse,
            "description": (
                "Four distinct codes at one status, so a client can tell a "
                "transient outage from a refusal about *you*: "
                "`matchmaking_unavailable`, `gate_data_unavailable`, "
                "`index_too_stale`, `search_not_recorded`."
            ),
        },
    },
    summary="Find me a game",
    description=(
        "Returns a ranked shortlist of at most **twenty** people worth "
        "messaging, **unpaginated** — there is no page two, and past the last "
        "row there is an honest empty state.\n\n"
        "**The breakdown ships with the search, not behind a tap.** Every term, "
        "its weight, its value, its contribution and the evidence it read ride "
        "on every row, because *Why 78?* has to open instantly.\n\n"
        "**Send asks, never facts.** Your radius, grid, tags, rating, intent "
        "and gender preference are read from your profile at request time. "
        "There is no per-search radius input.\n\n"
        "**Competitive and for fun select different weight vectors**, and the "
        "list visibly inverts between them.\n\n"
        "**Deliberately not idempotent.** Two taps are two searches.\n\n"
        "**Re-sorting costs no round trip:** `search.sorts_available` says "
        "which controls to draw, and a sort that would reorder nothing is not "
        "in it."
    ),
)
async def run_search(
    payload: RunSearchRequest,
    request: Request,
    user: CurrentUserDep,
    use_case: RunShortlistSearchDep,
) -> ShortlistResponse:
    answer = await use_case.execute(
        RunShortlistSearchCommand(
            searcher_id=user.id,
            sport=payload.sport,
            mode=payload.mode,
            # The request's own `X-Request-ID`, so that *"it showed me somebody
            # strange"* reaches the exact log line a year later.
            trace_id=trace_id_for(request),
        )
    )
    return render(answer)
