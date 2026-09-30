"""The player surface's proposal routes: the three answers to a card, and the
reader's live yeses (#538; the mechanics §6, §10.2; the screens A2.4, A7.3).

Mounted on the player surface (``app/api/v1/player.py``). Every route takes a
player's token and answers for that player only.

**A yes and a no are silent**: nothing here tells anybody anything, and a
repeated tap records nothing. **Nothing is charged by a yes** — the fill that
charges every seat together is the next ticket's (#541); this route's answer
already says how many seats are still open, so a nought is where it will hand
over.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Response, status

from app.core.exception_handlers import ErrorResponse
from app.modules.proposals.application.commands import AnswerProposalCommand
from app.modules.proposals.presentation.dependencies import (
    ReadLiveYesesDep,
    SayNoDep,
    SayYesDep,
    WithdrawYesDep,
)
from app.modules.proposals.presentation.schemas import (
    LiveYesesResponse,
    YesAnswerResponse,
)
from app.modules.users.presentation.dependencies import CurrentUserDep

router = APIRouter(prefix="/proposals", tags=["proposals"])
players_router = APIRouter(prefix="/players/me", tags=["proposals"])

_NOT_FOUND: dict[int | str, dict[str, Any]] = {
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponse,
        "description": (
            "`proposal_not_found` — no such game **for this player**: it does not "
            "exist, it was never dealt to them, or (for a yes) they are no longer "
            "in its group. One code for all three."
        ),
    },
}

_OVER = (
    "`proposal_is_over` — the game is no longer filling, named by "
    "`details.standing` (`EXPIRED` once its book-by passed, `WITHDRAWN` once its "
    "poster took the post back with nobody else In). The card leaves."
)


@router.post(
    "/{proposal_id}/yes",
    response_model=YesAnswerResponse,
    status_code=status.HTTP_200_OK,
    responses={
        **_NOT_FOUND,
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": (
                _OVER + " `proposal_already_answered` — this player said no: the "
                "card does not come back. "
                "`proposal_is_full` — every seat is In. "
                "`payment_method_required` — no saved payment method: save one, "
                "then say yes. `live_yeses_exhausted` — `details.cap` live yeses "
                "in `details.sport` already. `no_longer_fits` — somebody In now is "
                "somebody this player does not fit; the card has gone, and who is "
                "not said. Nothing was recorded."
            ),
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ErrorResponse,
            "description": (
                "`block_state_unavailable` — whether this player fits the people "
                "In could not be read. Nothing was recorded; retry."
            ),
        },
    },
    summary="Say yes to a game",
    description=(
        "*I'm in — if everybody is, book it and charge my share.* **Silent, free, "
        "and it holds nothing**: no money moves, no court is held, nobody is told "
        "(the others see the player In on the card). Yeses are the game's, not a "
        "version's: a yes on any version counts toward the one game. A yes "
        "already said records nothing and answers the same."
    ),
)
async def say_yes(
    proposal_id: UUID, user: CurrentUserDep, say: SayYesDep
) -> YesAnswerResponse:
    answer = await say.execute(
        AnswerProposalCommand(proposal_id=proposal_id, player_id=user.id)
    )
    return YesAnswerResponse.from_answer(answer)


@router.post(
    "/{proposal_id}/no",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    responses={
        **_NOT_FOUND,
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": (
                _OVER + " `proposal_already_answered` — this player is In: they "
                "leave by withdrawing their yes, never by a no."
            ),
        },
    },
    summary="Say no to a game",
    description=(
        "A swipe left: **silent, final, and never on the player's record.** The "
        "card does not come back. A second no records nothing."
    ),
)
async def say_no(proposal_id: UUID, user: CurrentUserDep, say: SayNoDep) -> Response:
    await say.execute(AnswerProposalCommand(proposal_id=proposal_id, player_id=user.id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/{proposal_id}/yes",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    responses={
        **_NOT_FOUND,
        status.HTTP_409_CONFLICT: {"model": ErrorResponse, "description": _OVER},
    },
    summary="Withdraw a yes",
    description=(
        "*Withdraw* on a You're In row: free and silent until the game fills. The "
        "seat is open again, and the player may say yes again while it fills. "
        "Withdrawing a yes never said records nothing. **A poster withdrawing "
        "with nobody else In "
        "takes the post with them**; with others In, the game carries on without "
        "them."
    ),
)
async def withdraw_yes(
    proposal_id: UUID, user: CurrentUserDep, withdraw: WithdrawYesDep
) -> Response:
    await withdraw.execute(
        AnswerProposalCommand(proposal_id=proposal_id, player_id=user.id)
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@players_router.get(
    "/live-yeses",
    response_model=LiveYesesResponse,
    summary="My live yeses",
    description=(
        "Every yes of the reader's on a game that has not filled, **across "
        "groups**, soonest game first, each with the share it would charge — You "
        "› Payments' *LIVE YESES*. A game past its book-by is not here, whether "
        "or not its expiry has been recorded."
    ),
)
async def read_live_yeses(
    user: CurrentUserDep, read: ReadLiveYesesDep
) -> LiveYesesResponse:
    return LiveYesesResponse.from_live(await read.execute(user.id))
