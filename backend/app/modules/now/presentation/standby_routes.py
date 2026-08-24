"""`DELETE /api/v1/matches/{matchId}/standby` — leaving the queue, in one tap.

ADR-0087's seventh act, and the one route off Now that is **a write and not a
screen**. A route exists to hold a consequence; leaving standby has none — no
seat, no money, no cascade, no outcome, and no position to forfeit, because a
standby position is a fact the platform refuses to show precisely so that it can
rise.

**It lives in ``now/`` although its path says ``matches``**, for the reason the
departure route does: the answer is Now's own update, and Now already reads
Matches everywhere in this tree. The alternative points the module graph both
ways for the sake of a URL.

**Not folded into the departure route**, and ADR-0087 says why: a match a player
is only on standby for is a match she holds no seat in, where ``mayDepart`` is
false — so the two acts never appear together on one card, and giving this one a
screen would be building the surface that ADR argued it does not need.

**No idempotency key.** ADR-0030's log is for *destructive* commands, and a
repeated delete of a place she no longer holds is the state she asked for.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Path, status

from app.modules.now.application.standby import LeaveStandbyCommand
from app.modules.now.presentation.dependencies import LeaveStandbyDep
from app.modules.now.presentation.schemas import StandbyWriteResponse
from app.modules.users.presentation.dependencies import CurrentUserDep

router = APIRouter(prefix="/matches", tags=["matches"])

_MATCH = Path(description="The match whose standby queue this is about.")


@router.delete(
    "/{match_id}/standby",
    response_model=StandbyWriteResponse,
    status_code=status.HTTP_200_OK,
    summary="Leave this match's standby queue, and correct Now off the same tap",
)
async def leave_standby(
    current_user: CurrentUserDep,
    use_case: LeaveStandbyDep,
    match_id: UUID = _MATCH,
) -> StandbyWriteResponse:
    """Take the viewer off the queue, and say what her screen should now hold.

    **200 and a body, not 204.** ADR-0074 has every action off Now return Now's
    update in the same response, so the screen corrects itself off her own tap
    rather than paying a full compose on the way back; a no-content answer would
    make this the one act that does not.

    **Deleting a place she does not hold answers exactly what a success
    answers.** Anybody may queue for any match, so there is no membership to be
    a stranger to and nothing here can refuse: the only 404 is a match id that
    names nothing, which is about the address rather than about the act.
    """

    update = await use_case.execute(
        LeaveStandbyCommand(player_id=current_user.id, match_id=match_id)
    )
    return StandbyWriteResponse.from_domain(update)
