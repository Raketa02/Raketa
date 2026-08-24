"""`/api/v1/matches/{matchId}/result` — the conversation, and joining it.

ADR-0074's route, and ADR-0060's before it. **A general ``GET /matches/{id}`` is
not here, and its absence is the decision** — it would author the match-detail
screen's contract inside a ticket that is not about it, and be the attractive
nuisance every later screen reaches for instead of asking for what it needs.
``matches`` enters the player contract through sub-paths of two screens, which is
a shape the detail screen did not choose, and that is the cheaper of the two
bills.

**It lives in ``now/`` although its path says ``matches``**, for the reason the
departure route does: the answer is Now's vocabulary end to end — the same spine,
the same situation half, the same card, Now's update — and Now already reads
Matches everywhere in this tree. Putting it in ``matches/`` would point the
module graph both ways at once for the sake of a URL.

**Two writes and not ADR-0074's three**, and the difference is which side of the
wire a rule sits on. Entering, correcting and countering are one act at three
moments: ADR-0048 caps *proposals per side* across all three, and which one a
given score is depends on what is already on the table. A client picking between
two endpoints would be holding exactly that rule — the one thing ADR-0053 leaves
the phone none of — so the score goes to one address and the server decides what
it was. The three booleans it is told back are three **labels** over these two
sends, which is what ADR-0074 asked for: *"the server states the acts… and the
phone derives none of them."*

**A bare rejection is refused by having no shape at all.** There is no endpoint
and no body that can express one; ADR-0048 requires a counter to carry a score,
and the way to make that true is to leave nowhere to say *no* — not a validator
that turns one away.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Path, status

from app.modules.now.application.result import (
    AcceptCommand,
    ProposeCommand,
    ResultQuery,
)
from app.modules.now.presentation.dependencies import (
    AcceptResultDep,
    ProposeResultDep,
    ReadResultDep,
)
from app.modules.now.presentation.result_schemas import (
    ProposeScoreRequest,
    ResultScreenResponse,
    ResultWriteResponse,
)
from app.modules.users.presentation.dependencies import CurrentUserDep

router = APIRouter(prefix="/matches", tags=["matches"])

_MATCH = Path(description="The match this result is about.")


@router.get(
    "/{match_id}/result",
    response_model=ResultScreenResponse,
    status_code=status.HTTP_200_OK,
    summary="What this match's result conversation is doing, and what she may do",
)
async def read_result(
    current_user: CurrentUserDep,
    use_case: ReadResultDep,
    match_id: UUID = _MATCH,
) -> ResultScreenResponse:
    """One reader, five renderings, off the same ladder a card resolves on.

    **Anyone who held a seat when the match ended resolves normally — including a
    leaver — with the three booleans false where ADR-0048 says so.** The leaver
    is the case that proves the rule: she played half an evening and paid for it,
    and a 404 would tell her the match never existed, which is the class of
    defect ADR-0030 was written against. A match still forming resolves to its
    forming situation with an empty result block — dull, correct, and not a
    special case. **A stranger gets a 404**, and that is authorisation rather
    than a state of the match.
    """

    screen = await use_case.execute(
        ResultQuery(player_id=current_user.id, match_id=match_id)
    )
    return ResultScreenResponse.from_domain(screen)


@router.post(
    "/{match_id}/result",
    response_model=ResultWriteResponse,
    status_code=status.HTTP_200_OK,
    summary="Put a score on the table, and correct Now off the same tap",
)
async def propose_score(
    current_user: CurrentUserDep,
    use_case: ProposeResultDep,
    body: ProposeScoreRequest,
    match_id: UUID = _MATCH,
) -> ResultWriteResponse:
    """Enter a score, correct her own side's, or counter the other side's.

    **200 and not 201**: nothing is created at an address a client could then
    fetch — the score is a fact about a match, read back through this same route
    and through the card on Now.

    **A refusal is not a second shape.** A side that has already spoken, a result
    that settled while her screen was open, a deadline that ran out, a leaver
    tapping through a stale screen — every one of them comes back as what a
    success returns, so the client has one code path and the player *sees* the
    correction rather than being told it. The one exception is a score no format
    of this sport could produce, which is about what she typed rather than about
    what the match is doing: a recomposed screen would show her the same table
    and no reason at all.
    """

    answer = await use_case.execute(
        ProposeCommand(
            player_id=current_user.id,
            match_id=match_id,
            sets=body.pairs(),
        )
    )
    return ResultWriteResponse.from_domain(answer)


@router.post(
    "/{match_id}/result/acceptance",
    response_model=ResultWriteResponse,
    status_code=status.HTTP_200_OK,
    summary="Agree with the score on the table, and correct Now off the same tap",
)
async def accept_result(
    current_user: CurrentUserDep,
    use_case: AcceptResultDep,
    match_id: UUID = _MATCH,
) -> ResultWriteResponse:
    """Agree, from the opposing side, with what is on the table.

    **A separate address because it carries nothing**, not because it is a
    different kind of thing: a body-less agreement posted to the same path as a
    score would be one endpoint whose meaning depended on whether a field was
    present, which is the *not there / there and empty* confusion the result
    block itself is shaped to avoid.

    **A stale accept is ADR-0074's own named case** and comes back as the
    counter's situation with `may_accept` false. So does a second tap on a result
    that has already settled, and so does silence having settled it first.
    """

    answer = await use_case.execute(
        AcceptCommand(player_id=current_user.id, match_id=match_id)
    )
    return ResultWriteResponse.from_domain(answer)
