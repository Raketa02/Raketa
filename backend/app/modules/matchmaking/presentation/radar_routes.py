"""The reading — the radar's one route, and the fifth surface of this module.

**One reading, one `search_id`, every player in the reach.** A reading is a
recorded search like a deal is: its rows are kept with their Fit and breakdown
for ever (``docs/adr/0104``), the record sheet opens from every card it drew
(``docs/adr/0159`` §3), and an answer given on it names it as its origin. It
crosses in the deal's shape — the same envelope, the same row — plus the two
fields only a drawn spot needs: a bearing, and the sport chips.

**No mode, no radius, no position, no week.** The sport is the whole ask
(``the-radar.md`` §2): the radar scores under the deck's ruler for everybody,
the reach is the viewer's own Search radius, the server holds the viewer's
cell, and a reading ranks nobody.

**Five gates asked, no judgement after them** (``docs/adr/0174`` §3). Blocked
either way, held, disabled, gender preference both ways, rated in the sport —
and then everyone inside the exact circle is drawn, each with a Fit the card
prints as served: Karol with a court, Magda passed on, Marek matched, a Level
the deck would never deal. There is no floor, no cool-off, no pass memory and
no dealt memory on the radar.

**A reading is not a deal** (§4). It enters no dealt memory, spends no hand
and notes no exposure; Monday's look changes nothing about Tuesday's deck. What
does reach the deck is an answer — `POST /interest` and `POST /passes` take a
reading's `search_id` as they take a deal's — and the person answered stays
on the radar either way.

**The chip is the deck's number** (§5). `pool.want_to_play_you` here is
computed by the deck's own rule over the deck's own gates, so the chip on
either pane of Players is one number; omitted at zero.
"""

from __future__ import annotations

from fastapi import APIRouter, Request, status

from app.core.exception_handlers import ErrorResponse
from app.core.tracing import trace_id_for
from app.modules.matchmaking.application.commands import RunRadarReadingCommand
from app.modules.matchmaking.presentation.dependencies import (
    CardPhotoLinksDep,
    RunRadarReadingDep,
)
from app.modules.matchmaking.presentation.rendering import render_reading
from app.modules.matchmaking.presentation.schemas import (
    ReadRadarRequest,
    ShortlistResponse,
)
from app.modules.users.presentation.dependencies import CurrentUserDep

router = APIRouter(prefix="/radar", tags=["radar"])


@router.post(
    "",
    response_model=ShortlistResponse,
    # The same rule the searches and deck routers are declared under: a field
    # this module never set is genuinely absent from the JSON rather than
    # present as `null`.
    response_model_exclude_unset=True,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": (
                "One reading: every player the radar may draw for you in this "
                "sport, ordered by distance and then id, sharing one "
                "`search_id`. **An empty reading is also a 200** — nobody rated "
                "in this sport inside your reach is an answer, and the pool it "
                "came from is described either way."
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
                "radius or an area from.\n\n"
                "**Never `play_intent_not_declared`**: like the deck, the radar "
                "reads no declaration."
            ),
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ErrorResponse,
            "description": (
                "`matchmaking_unavailable`, `gate_data_unavailable`, "
                "`index_too_stale`, `search_not_recorded` — four distinct codes "
                "at one status, so a client can tell a transient outage from a "
                "refusal about *you*. A gate that cannot be evaluated refuses "
                "the whole reading rather than drawing anybody it could not "
                "check."
            ),
        },
    },
    summary="Read the radar",
    description=(
        "Every player rated in this sport inside your reach, at their distance "
        "and bearing — the population the deck deals from, with the deck's "
        "reach and none of its judgement.\n\n"
        "**The sport is the whole ask.** No mode (every pairing scores under "
        "the deck's ruler), no radius (the reach is your own Search radius — "
        "there is no city), no position (the server holds your area), no "
        "week.\n\n"
        "**Five gates and nothing after them.** Blocked either way, under a "
        "hold, disabled, a gender preference either way, and rated in the "
        "sport — then everyone inside the circle is drawn, each with a `fit` "
        "printed as served. No level band, no quality floor, no cool-off, no "
        "pass memory, no dealt memory: somebody you have a court with, "
        "somebody you said *not today* to and somebody you are matched with "
        "are all on the radar.\n\n"
        "**Each row carries `bearing_deg` beside `distance_km`** — north `0`, "
        "clockwise, spot to spot, served and never derived — and `ratings[]`, "
        "every sport the player is rated in with their Level. Both are on the "
        "row and never inside `player_card`. The rows are ordered by distance "
        "and then by id, so a position means something.\n\n"
        "**`pool.want_to_play_you` is the deck's number.** Computed by the "
        "deck's own rule — its gates and its exclusions — so the chip here and "
        "the chip on the deck are one number; omitted at zero. Somebody who "
        "said yes to you whom the deck would never deal is still drawn, "
        "carrying `inclusion_reason: INTEREST_LIFT`, and is not counted.\n\n"
        "**A reading is not a deal.** It never enters the dealt memory: browse "
        "on Monday and do nothing, and Tuesday's deck deals the same people. "
        "Only an answer reaches the deck — `POST /interest` and `POST /passes` "
        "take this `search_id` exactly as they take a deal's — and after "
        "either the person **stays on the radar**.\n\n"
        "**Read it back** through `GET /api/v1/searches/{id}`, in this same "
        "shape, minus the chip — it is true of the moment the reading ran."
    ),
)
async def read_the_radar(
    payload: ReadRadarRequest,
    request: Request,
    user: CurrentUserDep,
    use_case: RunRadarReadingDep,
    photos: CardPhotoLinksDep,
) -> ShortlistResponse:
    answer = await use_case.execute(
        RunRadarReadingCommand(
            searcher_id=user.id,
            sport=payload.sport,
            trace_id=trace_id_for(request),
        )
    )
    return render_reading(answer, await photos.links_for(answer.record.returned))
