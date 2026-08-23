"""`/api/v1/matches/{matchId}/departure` — what leaving is worth, and leaving.

ADR-0086's route, which is ADR-0074's shape *"deliberately and without
variation"* — that ADR closed by recording that every future action off Now has
a pattern to copy rather than a question to reopen, and this is the first one to
take it up.

**A general ``GET /matches/{id}`` is not here, and its absence is the decision.**
It would author the match-detail screen's contract inside a ticket that is not
about it, and be the attractive nuisance every later screen reaches for instead
of asking for what it needs. ``matches`` enters the player contract as a
resource through a sub-path of a screen, which is a shape the detail screen did
not choose — and that is the cheaper of the two bills.

**It lives in ``now/`` although its path says ``matches``.** The answer is Now's
vocabulary end to end — the same spine, the same situation half, the same card,
Now's update — and Now already reads Matches everywhere in this tree. Putting it
in ``matches/`` would point the module graph both ways at once for the sake of a
URL. The write reaches the aggregate through a port of Now's own, which is the
shape ``money.Seats`` already takes over the same aggregate.

**One button, no third step.** The route *is* the confirmation: a dialog over a
screen whose whole job is to state the consequence asks the same question twice,
and the refuse-and-re-present rule already gives her the only correction that
matters — what is true now.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Path, status

from app.modules.now.application.departure import DepartCommand, DepartureQuery
from app.modules.now.presentation.departure_schemas import (
    DepartRequest,
    DepartureScreenResponse,
    DepartureWriteResponse,
)
from app.modules.now.presentation.dependencies import (
    MakeDepartureDep,
    ReadDepartureDep,
)
from app.modules.users.presentation.dependencies import CurrentUserDep

router = APIRouter(prefix="/matches", tags=["matches"])

_MATCH = Path(description="The match this departure is about.")


@router.get(
    "/{match_id}/departure",
    response_model=DepartureScreenResponse,
    status_code=status.HTTP_200_OK,
    summary="What leaving this match is worth, and what it could still become",
)
async def read_departure(
    current_user: CurrentUserDep,
    use_case: ReadDepartureDep,
    match_id: UUID = _MATCH,
) -> DepartureScreenResponse:
    """All four outcomes, the one that is live, and whether she may act on it.

    **A leaver resolves rather than 404s**, which is ADR-0074's own hardest case
    kept: a 404 tells her the match never existed, and that is the class of
    defect ADR-0030 was written against. The stranger is the only 404 here, and
    it is authorisation rather than a state of the match.
    """

    screen = await use_case.execute(
        DepartureQuery(player_id=current_user.id, match_id=match_id)
    )
    return DepartureScreenResponse.from_domain(screen)


@router.post(
    "/{match_id}/departure",
    response_model=DepartureWriteResponse,
    status_code=status.HTTP_200_OK,
    summary="Leave this match, and correct Now off the same tap",
)
async def make_departure(
    current_user: CurrentUserDep,
    use_case: MakeDepartureDep,
    body: DepartRequest,
    match_id: UUID = _MATCH,
) -> DepartureWriteResponse:
    """Leave at the quoted outcome, and hand back both screens.

    **200 and not 201**: nothing is created at an address a client could then
    fetch — the departure is a fact about a match, read back through this same
    route and through the card on Now.

    **A refusal is not a second shape.** A quote that has fallen, a match that
    has started or been cancelled, ADR-0046's lock, a second tap by somebody who
    has already left — every one of them comes back here as what a success
    returns, so the client has one code path and the player *sees* the
    correction rather than being told it.
    """

    answer = await use_case.execute(
        DepartCommand(
            player_id=current_user.id,
            match_id=match_id,
            quote=body.quote,
            idempotency_key=body.idempotency_key,
        )
    )
    return DepartureWriteResponse.from_domain(answer)
