"""``POST /api/v1/matches/{matchId}/seat`` — taking the seat an offer named.

The surface the offers region's one act arrives with (ADR-0083), and what it
opens is ADR-0081's five minutes rather than a seat: *"a seat is never taken
until it is paid, and what a player takes while she pays is a seat claim."*

**It lives in ``now/`` although its path says ``matches``**, for the reason the
departure, result and standby routes do: the answer is Now's vocabulary end to
end — the same card, the same update, the same two regions — and ``now`` already
reads ``matches`` everywhere in this tree. The alternative points the module graph
both ways for the sake of a URL.

**A refusal is not a second shape** (ADR-0070). Somebody else took it, the match
filled, joining closed, it started, it was cancelled, she is already in it: all
six answer with **what a success answers**, so the player *sees* that the seat has
gone rather than being told by a dialog. The two that answer differently are the
two that are about *her* rather than about the seat — she is already buying a seat
somewhere else, or she let this one go thirty seconds ago — and neither could be
said by recomposing a card about this match.

**No idempotency key.** ADR-0030's log is for *destructive* commands. A second tap
by the player who already holds the claim is refused by her own claim, and what a
key would buy — *did my first tap land* — is answered by the card that comes back
carrying it.

**No body.** Which seat is the match's answer and not the caller's
(``Match.open_claim``), and a price is not something the caller quotes: the sport
chip is a fact about the screen and rides as a query parameter, exactly as it does
on ``GET /api/v1/now``.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Path, Query, status

from app.modules.now.application.commands import SportFilter
from app.modules.now.application.seat import TakeSeatCommand
from app.modules.now.presentation.dependencies import TakeTheSeatDep
from app.modules.now.presentation.seat_schemas import SeatWriteResponse
from app.modules.users.presentation.dependencies import CurrentUserDep

router = APIRouter(prefix="/matches", tags=["matches"])

_MATCH = Path(description="The match a seat is being taken in.")


@router.post(
    "/{match_id}/seat",
    response_model=SeatWriteResponse,
    status_code=status.HTTP_200_OK,
    summary="Take a free seat, and correct Now off the same tap",
)
async def take_seat(
    current_user: CurrentUserDep,
    use_case: TakeTheSeatDep,
    match_id: UUID = _MATCH,
    sport: SportFilter = Query(
        default=SportFilter.ALL,
        description=(
            "The chip on the sport bar when the seat was tapped. The two regions "
            "this answers with are recomposed under it, so that a filtered screen "
            "is not replaced by an unfiltered one."
        ),
    ),
) -> SeatWriteResponse:
    """Open her five minutes in front of a free seat, and answer with the screen.

    **200 and a body, not 201.** ADR-0074 has every action off Now return Now's
    update in the same response, and what a claim creates is not a resource the
    client addresses — it is five minutes on a card it already holds.

    **Nothing is refused but the address.** Anybody may buy a free seat in any
    match: ``Match.open_claim`` is how *any* seat is taken from the marketplace,
    and *offered seats behave differently* is a second rule nobody would
    remember. The only 404 is a match id that names nothing.
    """

    answer = await use_case.execute(
        TakeSeatCommand(
            player_id=current_user.id, match_id=match_id, sport=sport
        )
    )
    return SeatWriteResponse.from_domain(answer)
