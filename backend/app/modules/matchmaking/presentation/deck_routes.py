"""The Players deal, and *not today* — the deck, and the quietest control beside it.

**One deal, one `search_id`, at most ten cards.** One-at-a-time is how the deck
is *shown*, not how it is computed: the ordering policy is a property of a whole
deal, and per-card searches would make the deck the highest-volume writer in the
system for no analytic gain.

**No mode, and no declaration** (``docs/adr/0169`` §2). Every deal scores under
the fun ruler for every viewer, declared or not, and the intent term stands down
on every card so that a declaration moves nobody. The deck is a discovery
surface; *who would I like to play with?* is not a question about the kind of
evening, and a player who never answered that question is dealt without being
asked to.

**The week is the one ask beside the sport.** It is an ask like the shortlist's
— it writes no profile, and the offer to save it rides back on the response —
kept so a client that runs a deal on an edited week is ranked on that week.

**The envelope says two numbers no other surface can** (``docs/adr/0169`` §4,
§5): how many eligible people are beyond this hand, and how many people are
waiting on the viewer. Both are counts and never lists; nothing here names who.

**Somebody the viewer is already with is not dealt** (``docs/adr/0169`` §6): a
live challenge or game between the two holds them out, and for thirty days after
the court is behind them. Deck only — Find a game lists them throughout.

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

**And a pass can be cleared, by one route** (``docs/adr/0169`` §5). *Show them
again* is `POST /deck/reset` with the sport: every pass suppression, the day's
dealt memory and the cool-off lift together, for that sport only; the durable
pass record stays, so a re-shown card is still a re-show; live yeses are not
touched. It answers `204` for the reason the pass does — there is no shape a
reset crosses the wire in — and pressing it twice is one press.
"""

from __future__ import annotations

from fastapi import APIRouter, Request, Response, status

from app.core.exception_handlers import ErrorResponse
from app.core.tracing import trace_id_for
from app.modules.matchmaking.application.commands import (
    RecordPassCommand,
    ResetDeckCommand,
    RunDeckDealCommand,
)
from app.modules.matchmaking.presentation.dependencies import (
    CardPhotoLinksDep,
    RecordPassDep,
    ResetDeckDep,
    RunDeckDealDep,
)
from app.modules.matchmaking.presentation.rendering import render_deal
from app.modules.matchmaking.presentation.schemas import (
    DealDeckRequest,
    RecordPassRequest,
    ResetDeckRequest,
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
                "`player_profile_not_committed` — there is no profile to read a "
                "radius, a grid or an area from.\n\n"
                "**Never `play_intent_not_declared`**: the deck reads no "
                "declaration, so a player who never made one is dealt without "
                "being asked to."
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
    summary="Deal the deck",
    description=(
        "Deals one batch of cards: one judgement at a time, no mode to pick and "
        "no setup.\n\n"
        "**No mode, in either direction, and no declaration read.** Every deal "
        "scores under the same ruler for every viewer — shared tags lead, "
        "overlap second, a wide level window — whatever either of you declared, "
        "and a player who never declared is dealt without being asked to. On "
        "every card `INTENT_ALIGNMENT` is in `degraded_terms` as "
        "`NOT_READ_ON_THIS_SURFACE`, which is the surface's doing and says "
        "nothing about the person.\n\n"
        "**Send `availability_override` if the player edited their week**, and "
        "the deal runs on it; omit it and the grid on the profile is used. It "
        "writes nothing: the deal comes back with a `KEEP_THESE_TIMES` prompt, "
        "and saving is a separate request the player makes. **A cleared week is "
        "a legal value** — unticking every cell deals a deck rather than being "
        "refused.\n\n"
        "**A spent deal deals again.** Post again for a new deal with a new "
        "`search_id`; running out of cards is not running out of people, and "
        "only a fresh deal that comes back empty means the pool is thin. "
        "`pool.remaining` says how many eligible people are beyond this hand, "
        "and drops as hands are dealt.\n\n"
        "**`pool.want_to_play_you`** says how many people have a live *Let's "
        "play* towards you that would be dealt — a count, never a list, and `0` "
        "when nobody is waiting. Somebody who said yes to you is dealt "
        "**unmarked**: they carry `inclusion_reason: INTEREST_LIFT` and nothing "
        "else says so, and they sit where their lift puts them rather than "
        "first by rule.\n\n"
        "**Somebody you already have a court with is not dealt** — a live "
        "challenge or game, and for the cool-off after it is behind you, which "
        "is a ruleset window (thirty days at release) and never crosses the "
        "wire. Find a game still lists them.\n\n"
        "**The order is the deck's variety**: the people Liveness lifted, the "
        "ones who said yes among them, then the rest. There is no re-sort — "
        "`sorts_available` is empty here, because a deck is one card at a "
        "time.\n\n"
        "**No widening is offered.** `rung_offers` is `null` on a deal: the "
        "relaxation ladder belongs to the shortlist.\n\n"
        "**Read it back** through `GET /api/v1/searches/{id}`, in this same "
        "shape, minus the two counts — they are true of the moment the hand was "
        "dealt."
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


@router.post(
    "/reset",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": (
                "Cleared. **Nothing is returned** — the next deal is where the "
                "difference shows."
            ),
        },
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorResponse,
            "description": "`account_held` — this account is under a live hold.",
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": (
                "`sport_not_rated` — you hold no rating for this sport, so there "
                "is no deck of yours to deal again."
            ),
        },
    },
    summary="Show them again",
    description=(
        "Deals your deck whole again, for one sport.\n\n"
        "**Three things lift at once, and only for this sport**: every *Not "
        "today* you gave, the people you were dealt today, and the cool-off on "
        "anybody you have had a court with. The next `POST /deck` deals all of "
        "them. What stays: the people you have a live *Let's play* on are still "
        "yours to wait on, another sport's deck is untouched, and the record "
        "that you once passed on somebody is kept — a card you see again is "
        "still one you have seen.\n\n"
        "**Idempotent.** Pressing it twice in a row is one press.\n\n"
        "**Nobody is told**, and nothing is returned. The only place a reset "
        "shows is your own next deal."
    ),
)
async def show_them_again(
    payload: ResetDeckRequest,
    user: CurrentUserDep,
    use_case: ResetDeckDep,
) -> Response:
    await use_case.execute(ResetDeckCommand(player_id=user.id, sport=payload.sport))
    # Built here rather than returned as `None`, for the pass's reason: the
    # route's declared `204` and what it sends cannot come apart.
    return Response(status_code=status.HTTP_204_NO_CONTENT)


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
