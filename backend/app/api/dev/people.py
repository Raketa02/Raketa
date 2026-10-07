"""A person's row: *Yes*, *No* and *Withdraw* on the cards they were dealt, as
them (``docs/adr/0194`` §2, §3; #590).

**Each route is the player's own route with the acting account in place of the
signed-in one** — ``POST /dev/as/{player_id}/proposals/{id}/yes`` beside the
player's ``POST /api/v1/proposals/{id}/yes`` — and runs the same use case,
built by the same dependency, with the same command. So a press does what that
person's own button would do, **refusals included**, and a refusal reaches the
page in the domain's own words, through the one error envelope.

**No logic of its own.** A route here is wiring: it builds the command and calls
the use case. If a player route ever does work outside its use case, the console
would skip it — that work moves into the use case, never into a copy here.
``tests/api/test_games_test_console.py`` holds each button to the player's route
over the same cases, refusals included.
"""

from __future__ import annotations

import app.api.dev.refusal  # noqa: F401 — refuses first; see refusal.py

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Response, status

from app.api.dev.accounts import ActingDep
from app.core.exception_handlers import ErrorResponse
from app.modules.proposals.application.commands import AnswerProposalCommand
from app.modules.proposals.presentation.dependencies import (
    SayNoDep,
    SayYesDep,
    WithdrawYesDep,
)
from app.modules.proposals.presentation.schemas import YesAnswerResponse

router = APIRouter(prefix="/as/{player_id}", tags=["dev"])

_REFUSED: dict[int | str, dict[str, Any]] = {
    status.HTTP_403_FORBIDDEN: {
        "model": ErrorResponse,
        "description": (
            "`not_a_seed_account` — the acting account is not one the seed "
            "created. Nothing was asked of the use case."
        ),
    },
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponse,
        "description": "As the player's own route answers it.",
    },
    status.HTTP_409_CONFLICT: {
        "model": ErrorResponse,
        "description": "As the player's own route answers it.",
    },
}


@router.post(
    "/proposals/{proposal_id}/yes",
    response_model=YesAnswerResponse,
    status_code=status.HTTP_200_OK,
    responses={
        **_REFUSED,
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ErrorResponse,
            "description": "As the player's own route answers it.",
        },
    },
    summary="Yes, as this person",
    description=(
        "`POST /api/v1/proposals/{id}/yes` as the acting account: the same use "
        "case, refusals included — and when it is the last, the fill, over the "
        "provider this process moves money through."
    ),
)
async def say_yes(
    proposal_id: UUID, acting: ActingDep, say: SayYesDep
) -> YesAnswerResponse:
    answer = await say.execute(
        AnswerProposalCommand(proposal_id=proposal_id, player_id=acting)
    )
    return YesAnswerResponse.from_answer(answer)


@router.post(
    "/proposals/{proposal_id}/no",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    responses=_REFUSED,
    summary="No, as this person",
    description=(
        "`POST /api/v1/proposals/{id}/no` as the acting account: silent, final, "
        "and never on their record."
    ),
)
async def say_no(proposal_id: UUID, acting: ActingDep, say: SayNoDep) -> Response:
    await say.execute(AnswerProposalCommand(proposal_id=proposal_id, player_id=acting))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/proposals/{proposal_id}/yes",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    responses=_REFUSED,
    summary="Withdraw, as this person",
    description=(
        "`DELETE /api/v1/proposals/{id}/yes` as the acting account — and while an "
        "On request club decides, *Leave the game*, which takes the request with "
        "it."
    ),
)
async def withdraw_yes(
    proposal_id: UUID, acting: ActingDep, withdraw: WithdrawYesDep
) -> Response:
    await withdraw.execute(
        AnswerProposalCommand(proposal_id=proposal_id, player_id=acting)
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
