"""⚡ *Fill the seats*, and *what would this four leave on court*.

**Two routes, and only one of them is a search.** ``POST /lineups`` seats people
and writes the durable row every engine invocation writes; ``POST /forecasts``
computes and records nothing at all, because re-posting a line-up per swap would
enter a six-edit builder session into *searches run* as six searches
(``docs/adr/0108``).

**A line-up and filling seats are one route**, and they differ by ``locked_seats``
being non-empty — a property of the request. Hand-seating somebody and pressing ⚡
is the same shape as ⚡ on an empty court, and ``search.surface`` records which of
the two happened without the client having chosen between them.

**Completing a challenge is a second such property, not a second route**
(``docs/adr/0150`` §2). ``completing_challenge_id`` names the half-built court
this fill finishes, and ``sport``, ``mode`` and ``locked_seats`` are refused
beside it: all three are facts that challenge already holds, and a caller
supplying one offers a second place for a fact to be true.

**A seat may be unfilled and the line-up is still a `200`.** A four contains six
pairs and every gate binds all of them (``docs/adr/0116``), so a four can be
impossible where candidates are plentiful — and *three of four* is an honest
answer with a reason on the empty seat, never an error. No seat is ever filled
below the quality floor to complete a four, a newcomer least of all.

**The group objective is never returned as a number.** It chose these four over
every other combination, and a second score the player must trust is worse than
none: it competes with Fit and nobody can act on it. What crosses instead is one
closed ``group_reason`` naming the term with the largest margin between the
winner and the runner-up.
"""

from __future__ import annotations

from fastapi import APIRouter, Request, status

from app.core.exception_handlers import ErrorResponse
from app.core.tracing import trace_id_for
from app.modules.matchmaking.application.commands import (
    ForecastLineupCommand,
    RunLineupSearchCommand,
)
from app.modules.matchmaking.presentation.dependencies import (
    CardPhotoLinksDep,
    ForecastLineupDep,
    RunLineupSearchDep,
)
from app.modules.matchmaking.presentation.rendering import (
    render_forecast,
    render_lineup,
)
from app.modules.matchmaking.presentation.schemas import (
    ForecastRequest,
    ForecastResponse,
    LineupResponse,
    RunLineupRequest,
)
from app.modules.users.presentation.dependencies import CurrentUserDep

router = APIRouter(prefix="/lineups", tags=["lineups"])
forecasts_router = APIRouter(prefix="/forecasts", tags=["forecasts"])


@router.post(
    "",
    response_model=LineupResponse,
    # The same rule the shortlist is declared under: an omitted field is
    # genuinely absent from the JSON rather than present as `null`, which is what
    # lets an unfilled seat and a taken one be told apart by presence.
    response_model_exclude_unset=True,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": (
                "A seated line-up, every arrangement with its own forecast, and "
                "one reason this four beat the runner-up. **A seat may be "
                "unfilled and this is still a 200** — the empty seat says why."
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
                "offered.\n\n"
                "`locked_seat_not_available` — somebody you seated by hand "
                "cannot be seated in this line-up. **Which one is deliberately "
                "not said.** Completing a challenge, this means somebody on your "
                "court has been blocked, held or deactivated since they "
                "accepted — re-read the challenge.\n\n"
                "`challenge_not_yours_to_fill` — the challenge you named is not "
                "one of yours to complete. **One code for three cases**: no such "
                "challenge, you hold no live seat on it, or nobody is arranging "
                "it any more."
            ),
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ErrorResponse,
            "description": (
                "`matchmaking_unavailable`, `gate_data_unavailable`, "
                "`index_too_stale`, `search_not_recorded`. The second one covers "
                "the **pairwise block mask**: a four is never seated on a gate "
                "that could not be evaluated."
            ),
        },
    },
    summary="Fill the seats",
    description=(
        "Seats a four — you and three others — chosen together rather than one "
        "at a time, and returns **all three arrangements** with a forecast "
        "each.\n\n"
        "**Every gate binds all six pairs.** A block, a gender preference and "
        "the level tolerance are checked between *every two* of the four, not "
        "just between you and each of them. That is stricter than a shortlist "
        "and it compounds: a four can be impossible where candidates are "
        "plentiful, and the honest answer is a partial line-up carrying "
        "`NO_ADMISSIBLE_COMBINATION`.\n\n"
        "**A seat is never filled below the quality floor** to complete a four, "
        "a newcomer least of all. *Three of four* is a real answer.\n\n"
        "**Swapping sides costs no round trip.** All three arrangements cross, "
        "each with `is_best` and `is_evenest` — two separate booleans, because "
        "they can differ, which happens precisely when the four's levels are "
        "near-equal and balance has nothing left to say.\n\n"
        "**Send `locked_seats` to hand-seat people.** From that moment the "
        "engine optimises **for the group** and says so in "
        "`search.optimised_for`, because you may end up with a worse individual "
        "match than an empty court would have given you.\n\n"
        "**Send `completing_challenge_id` to finish a half-built court**, and "
        "send nothing else about it: the sport, the kind of evening and the "
        "locked seats are read off that challenge. **Any live member may fill "
        "it** — only the withdraw is the organiser's. The people who accepted "
        "come back as ordinary rows so the builder can draw them, everybody who "
        "has already answered that challenge is out of its own pool, and the "
        "window is never re-stamped.\n\n"
        "**A lapsed invitee is unreachable in every sport until that challenge "
        "ends**, and the withdraw is the only thing that ends it. Somebody who "
        "let your invitation run out is neither a candidate for this fill nor "
        "for any other search of yours, in any sport, while the court still "
        "stands.\n\n"
        "**A seated card shows the same number the shortlist showed.** Nothing "
        "is re-scored when somebody sits down."
    ),
)
async def run_lineup(
    payload: RunLineupRequest,
    request: Request,
    user: CurrentUserDep,
    use_case: RunLineupSearchDep,
    photos: CardPhotoLinksDep,
) -> LineupResponse:
    answer = await use_case.execute(
        RunLineupSearchCommand(
            searcher_id=user.id,
            sport=payload.sport,
            mode=payload.mode,
            locked_seats=tuple(payload.locked_seats),
            completing_challenge_id=payload.completing_challenge_id,
            availability_override=(
                None
                if payload.availability_override is None
                else tuple(cell.as_cell() for cell in payload.availability_override)
            ),
            offered_by_search_id=payload.offered_by_search_id,
            rung=payload.rung,
            trace_id=trace_id_for(request),
        )
    )
    return render_lineup(answer, await photos.links_for(answer.record.returned))


@forecasts_router.post(
    "",
    response_model=ForecastResponse,
    response_model_exclude_unset=True,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": (
                "Every arrangement of the four you composed, each with its own "
                "forecast. **Provisional while a seat is empty**, and the "
                "provisional figure becomes exactly the final figure the moment "
                "the seat fills."
            ),
        },
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorResponse,
            "description": "`account_held` — this account is under a live hold.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": (
                "`search_not_found` — no search of yours showed all of those "
                "players. **One code for four cases**: the search does not "
                "exist, it is somebody else's, it was for another sport, or it "
                "never showed one of these people. Telling them apart would "
                "answer questions about strangers one probe at a time."
            ),
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": (
                "`sport_not_rated`, `play_intent_not_declared`, "
                "`player_profile_not_committed` — the same three the search "
                "route owes, for the same reason: a forecast puts **you** on the "
                "court."
            ),
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ErrorResponse,
            "description": (
                "`gate_data_unavailable` — blocks and holds are re-read live and "
                "a gate that cannot be evaluated excludes.\n\n"
                "`matchmaking_unavailable` — the engine raised."
            ),
        },
    },
    summary="Forecast a line-up you composed",
    description=(
        "Returns every arrangement of a four **you** put together, each with its "
        "own forecast — for the builder, where you swap somebody in and the "
        "number has to move.\n\n"
        "**This creates no search and records nothing.** Six swaps are not six "
        "searches, and recording them as such would put a lie in the one table "
        "the product judges itself by. There is no `search_id` in the response "
        "and nothing to read back.\n\n"
        "**Seats may be empty.** A side with one player is read as if the "
        "missing player matched the one already there; the forecast comes back "
        "`provisional` with its `assumption`, and the moment you fill the seat "
        "the number is **exactly** the same as the final one.\n\n"
        "**It is bound to a search you ran.** Every player you name must have "
        "appeared in that search's returned rows.\n\n"
        "**No forecast arithmetic belongs on the client.** Every figure the "
        "builder can show comes from here or from `/lineups`."
    ),
)
async def forecast_lineup(
    payload: ForecastRequest,
    user: CurrentUserDep,
    use_case: ForecastLineupDep,
) -> ForecastResponse:
    answer = await use_case.execute(
        ForecastLineupCommand(
            searcher_id=user.id,
            sport=payload.sport,
            mode=payload.mode,
            search_id=payload.search_id,
            players=tuple(payload.players),
        )
    )
    return render_forecast(answer)
