"""*Match me*, and *not today* — the deck, and the quietest control beside it.

**One deal, one `search_id`, at most ten cards.** One-at-a-time is how the deck
is *shown*, not how it is computed: the ordering policy is a property of a whole
deal, and per-card searches would make the deck the highest-volume writer in the
system for no analytic gain.

**No mode.** The deck reads the player's own declared Play intent for the sport,
maps *no preference* to *for fun*, and never selects a third vector. Indecision
is not a blocked state.

**The week is the one ask beside the sport.** *Match me* is reached from the same
screen the grid is edited on, so a deal that ignored the edit would rank on a
week the player had just replaced. It is an ask like the shortlist's — it writes
no profile, and the offer to save it rides back on the response.

**A spent deal deals again.** Running out of cards is not running out of people:
the next request is a new search with a new id, the same exclusions plus
everybody dealt recently, and only a fresh deal that comes back empty is the
honest empty state.

**A pass is write-only, and the two routers are here together because they are
one gesture's two halves.** The deck deals a card; a pass says *not that one*,
quietly, for a while, in this player's deck and nowhere else. No route in this
file — or in any other — returns a pass, in any shape, to anybody: not to the
passer, not as a count, not as a timestamp. That is why the pass answers `204`
and not a body.
"""

from __future__ import annotations

from fastapi import APIRouter, Request, Response, status

from app.core.exception_handlers import ErrorResponse
from app.core.tracing import trace_id_for
from app.modules.matchmaking.application.commands import (
    RecordPassCommand,
    RunDeckDealCommand,
)
from app.modules.matchmaking.presentation.dependencies import (
    CardPhotoLinksDep,
    RecordPassDep,
    RunDeckDealDep,
)
from app.modules.matchmaking.presentation.rendering import render_deal
from app.modules.matchmaking.presentation.schemas import (
    DealDeckRequest,
    RecordPassRequest,
    ShortlistResponse,
)
from app.modules.users.presentation.dependencies import CurrentUserDep

router = APIRouter(prefix="/deck", tags=["deck"])
passes_router = APIRouter(prefix="/passes", tags=["passes"])


@router.post(
    "",
    response_model=ShortlistResponse,
    # The same rule the searches router is declared under: a field this module
    # never set is genuinely absent from the JSON rather than present as `null`.
    response_model_exclude_unset=True,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": (
                "One deal: an ordered batch of at most ten cards, sharing one "
                "`search_id`. **An empty deal is also a 200** — a fresh deal "
                "that came back with nothing is the honest empty state, and the "
                "pool it came from is described either way."
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
                "`play_intent_not_declared` — the deck has no mode to read, so "
                "it reads your declaration; without one there is nothing at all "
                "to go on. **Answering *no preference* is an answer** and gives "
                "you a working deck.\n\n"
                "`player_profile_not_committed` — there is no profile to read a "
                "radius, a grid or an area from."
            ),
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ErrorResponse,
            "description": (
                "`matchmaking_unavailable`, `gate_data_unavailable`, "
                "`index_too_stale`, `search_not_recorded` — four distinct codes "
                "at one status, so a client can tell a transient outage from a "
                "refusal about *you*."
            ),
        },
    },
    summary="Match me",
    description=(
        "Deals one batch of cards: one judgement at a time, no mode to pick and "
        "no setup.\n\n"
        "**No mode, in either direction.** The deck reads your own declared "
        "Play intent for the sport — *no preference* still gives you a working "
        "deck — and no mode crosses the wire either way.\n\n"
        "**Send `availability_override` if the player edited their week** on "
        "the Play screen, and the deal runs on it; omit it and the grid on the "
        "profile is used. It writes nothing: the deal comes back with a "
        "`KEEP_THESE_TIMES` prompt, and saving is a separate request the player "
        "makes. **A cleared week is a legal value** — unticking every cell "
        "deals a deck rather than being refused.\n\n"
        "**A spent deal deals again.** Post again for a new deal with a new "
        "`search_id`; running out of cards is not running out of people, and "
        "only a fresh deal that comes back empty means the pool is thin.\n\n"
        "**The order is the deck's variety**: people who already said *Let's "
        "play* to you, then the liveliest, then the rest. There is no re-sort — "
        "`sorts_available` is empty here, because a deck is one card at a "
        "time.\n\n"
        "**No widening is offered.** `rung_offers` is `null` on a deal: the "
        "relaxation ladder belongs to the shortlist.\n\n"
        "**Read it back** through `GET /api/v1/searches/{id}`, in this same "
        "shape."
    ),
)
async def deal_the_deck(
    payload: DealDeckRequest,
    request: Request,
    user: CurrentUserDep,
    use_case: RunDeckDealDep,
    photos: CardPhotoLinksDep,
) -> ShortlistResponse:
    answer = await use_case.execute(
        RunDeckDealCommand(
            searcher_id=user.id,
            sport=payload.sport,
            availability_override=(
                None
                if payload.availability_override is None
                else tuple(
                    cell.as_cell() for cell in payload.availability_override
                )
            ),
            trace_id=trace_id_for(request),
        )
    )
    return render_deal(answer, await photos.links_for(answer.record.returned))


@passes_router.post(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": (
                "Recorded. **Nothing is returned, and nothing ever will be** — "
                "there is no route through which a pass reaches anybody, "
                "including you."
            ),
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": (
                "`origin_search_not_found` — no search of **yours** showed that "
                "player for that sport. The origin is refused rather than "
                "linked as null."
            ),
        },
    },
    summary="Not today",
    description=(
        "Keeps somebody out of **your deck** for a while, and reaches nothing "
        "else.\n\n"
        "**It is not a block, and it never becomes one.** You will still find "
        "that person in a shortlist tomorrow if you change your mind; it never "
        "touches their deck, and passing twice buys exactly the same window as "
        "passing once. The control that removes a person from a person is "
        "`POST /api/v1/blocks`, and it is meant to be the heavier gesture.\n\n"
        "**Nobody is told.** Not them, not you: no count, no list, no *show "
        "them again*.\n\n"
        "**`search_id` is required** — it says which deal this card came from."
    ),
)
async def record_a_pass(
    payload: RecordPassRequest,
    user: CurrentUserDep,
    use_case: RecordPassDep,
) -> Response:
    await use_case.execute(
        RecordPassCommand(
            passer_id=user.id,
            passed_id=payload.player_id,
            sport=payload.sport,
            search_id=payload.search_id,
        )
    )
    # Built here rather than returned as `None`, so the route's declared `204`
    # and what it actually sends cannot come apart: there is no body, and there
    # is no shape a body could be.
    return Response(status_code=status.HTTP_204_NO_CONTENT)
