"""*Find me a game*, and *show me that again* — two routes over one shape.

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

**The read-back returns the same schema, and it is not a cache.** The record is
immutable and never expires, so *Why 78?* opens a month later; but the gates that
fail closed are re-evaluated live, because a stored result that could resurrect
somebody who blocked the searcher in between is a safety hole wearing a cache's
clothes (``docs/adr/0109``). A row those gates no longer admit keeps its place in
the list and **states that it is withheld** — a list that quietly gets shorter is
the same class of lie as a breakdown that quietly stops adding up.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Path, Request, status

from app.core.exception_handlers import ErrorResponse
from app.core.tracing import trace_id_for
from app.modules.matchmaking.application.commands import RunShortlistSearchCommand
from app.modules.matchmaking.application.read_back_search import (
    ReadBackSearchCommand,
)
from app.modules.matchmaking.presentation.dependencies import (
    CardPhotoLinksDep,
    ReadBackSearchDep,
    RunShortlistSearchDep,
)
from app.modules.matchmaking.presentation.rendering import render, render_read_back
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
                "radius, a grid or an area from.\n\n"
                "`rung_offer_not_found` — you cited a rung no search of yours "
                "offered. The widening is read off the offer, never off the "
                "request, so an unknown citation is refused rather than run "
                "narrow and recorded as widened."
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
        "**Relaxation is offered, never applied.** When the shortlist comes "
        "back short the envelope carries `rung_offers` — your times, then your "
        "radius x1.5, then x2.0 — each with a **real** count from a genuine "
        "re-run and its own window. Taking one is a **new search citing this "
        "one**: post again with `offered_by_search_id` and `rung`. Your saved "
        "preferences stay yours, and **the quality floor is never relaxed**, so "
        "*nobody tonight* stays a real answer.\n\n"
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
    photos: CardPhotoLinksDep,
) -> ShortlistResponse:
    answer = await use_case.execute(
        RunShortlistSearchCommand(
            searcher_id=user.id,
            sport=payload.sport,
            mode=payload.mode,
            # Primitives, because building a grid is the domain's job and not
            # the boundary's.
            availability_override=(
                None
                if payload.availability_override is None
                else tuple(
                    cell.as_cell() for cell in payload.availability_override
                )
            ),
            offered_by_search_id=payload.offered_by_search_id,
            rung=payload.rung,
            # The request's own `X-Request-ID`, so that *"it showed me somebody
            # strange"* reaches the exact log line a year later.
            trace_id=trace_id_for(request),
        )
    )
    return render(answer, await photos.links_for(answer.record.returned))


@router.get(
    "/{search_id}",
    response_model=ShortlistResponse,
    # The same rule the `POST` is declared under, for the same reason: an
    # omitted field is genuinely absent from the JSON rather than present as
    # `null`. It is what makes `withheld` appear on a read-back and nowhere else.
    response_model_exclude_unset=True,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": (
                "The recorded answer, **plus live gate state**. The same schema "
                "the `POST` returned — not a fuller one and not a slimmer one — "
                "with any row the fail-closed gates no longer admit **stated as "
                "withheld** rather than quietly missing."
            ),
        },
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorResponse,
            "description": (
                "`account_held` — this account is under a live hold. The hold "
                "points both ways, and it points at old answers too."
            ),
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": (
                "`search_not_found` — no search of **yours** has that id. A "
                "search belonging to somebody else answers exactly as one that "
                "never existed."
            ),
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ErrorResponse,
            "description": (
                "`gate_data_unavailable` — a fail-closed gate could not be "
                "re-evaluated, so the answer is refused rather than served "
                "unverified.\n\n"
                "`matchmaking_unavailable` — there is no index in this process "
                "to read the other side of the gender gate from."
            ),
        },
    },
    summary="Read a shortlist back",
    description=(
        "Returns a search you ran earlier, in **the same shape the `POST` "
        "returned it**, so *Why 78?* opens as fast a month later as it did on "
        "the day.\n\n"
        "**The record is immutable; the gates are live.** Blocks, holds, "
        "account state and the mutual gender preference are re-evaluated at "
        "read time, and nothing is rewritten by doing so.\n\n"
        "**A row those gates now exclude is stated as withheld** — it keeps its "
        "place in the list, carries no person, and does not say which gate "
        "fired. Branch on `withheld`.\n\n"
        "**A searcher may read their own search and nobody else's.**"
    ),
)
async def read_search_back(
    user: CurrentUserDep,
    use_case: ReadBackSearchDep,
    photos: CardPhotoLinksDep,
    search_id: UUID = Path(..., description="The answer's identity, from the POST"),
) -> ShortlistResponse:
    answer = await use_case.execute(
        ReadBackSearchCommand(search_id=search_id, reader_id=user.id)
    )
    return render_read_back(answer, await photos.links_for(answer.shown))
