"""The three block endpoints: make one, lift one, and read your own.

**Making and lifting answer 204, always, with an empty body.** Blocking somebody
already blocked, unblocking somebody who was never blocked, blocking an id that
belongs to nobody — all three answer exactly as the ordinary case does, so no
answer here says anything about anybody else's block (``docs/adr/0193`` §3).

**The one read is your own** (``docs/adr/0193`` §3). ``GET /blocks`` lists the
blocks the caller made — whom, and when — and nothing anywhere lists who blocked
the caller. The blocked party is never told, and there is no route through which
they could be.

**No cap, no cooldown, no rate limit** (``docs/adr/0095`` §3). Nothing in this
router counts, and a limit added later would be a tax on the one control a person
has.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, status

from app.core.exception_handlers import ErrorResponse
from app.modules.blocks.application.commands import (
    BlockPlayerCommand,
    UnblockPlayerCommand,
)
from app.modules.blocks.presentation.dependencies import (
    BlockPlayerDep,
    ReadBlockedPlayersDep,
    UnblockPlayerDep,
)
from app.modules.blocks.presentation.schemas import (
    BlockedPlayersResponse,
    BlockPlayerRequest,
)
from app.modules.users.presentation.dependencies import CurrentUserDep

router = APIRouter(prefix="/blocks", tags=["blocks"])


@router.post(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": (
                "The block stands. Also the answer when it already stood — "
                "blocking is idempotent and a second call records nothing."
            ),
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": (
                "`cannot_block_yourself` — the caller named themselves as the "
                "other party."
            ),
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": (
                "`concurrent_modification` — two blocks of this player raced and "
                "this one lost. Retry: the retry is the idempotent no-op."
            ),
        },
    },
    summary="Block a player",
    description=(
        "**Keeps the two of you off one court**, immediately and silently, "
        "whichever of you made the block: you are never dealt a game together, "
        "never both In on one, never offered each other's seat and never joined "
        "onto each other's post. A yes that would put you together is refused "
        "without saying why.\n\n"
        "**It reaches nothing else.** You both stay in your groups and see each "
        "other in their Members lists, either of you can open the other's "
        "record, and a chat you already share keeps working.\n\n"
        "**Your yeses where they are In are taken back** — on a game still "
        "filling, as an ordinary withdrawal, and on a game waiting for its club "
        "as if you left it, so the others In are told you left. Theirs stand. A "
        "game the club confirmed is never touched: leaving it is the ordinary "
        "rule. Unblocking brings none of them back.\n\n"
        "**Idempotent.** Blocking somebody already blocked records nothing and "
        "answers 204.\n\n"
        "**No cap, no cooldown and no rate limit**, and none will be added.\n\n"
        "**There is no reason field.** A reason belongs to a report, and this is "
        "not one.\n\n"
        "**Neither side is notified.** You can read your own blocks — "
        "`GET /blocks`, and `blocked_by_you` on a record — and nothing in this "
        "API tells anybody they were blocked.\n\n"
        "**The record is directed and the effect is symmetric.** Your block of "
        "them and their block of you are independent: lifting yours never lifts "
        "theirs."
    ),
)
async def block_player(
    payload: BlockPlayerRequest,
    user: CurrentUserDep,
    use_case: BlockPlayerDep,
) -> None:
    await use_case.execute(
        BlockPlayerCommand(blocker_id=user.id, blocked_id=payload.player_id)
    )


@router.delete(
    "/{player_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": (
                "Your block of this player is lifted. Also the answer when there "
                "was nothing to lift — the two cases are deliberately "
                "indistinguishable."
            ),
        },
    },
    summary="Unblock a player",
    description=(
        "Lifts **your** block of this player, immediately: the two of you may be "
        "proposed together again. **It brings back no yes** the block took "
        "back.\n\n"
        "**It lifts one direction.** If they have also blocked you, that block "
        "stands and the two of you are still kept off one court — and nothing "
        "here tells you so.\n\n"
        "**Idempotent, and it never 404s.** Unblocking somebody you never "
        "blocked answers 204 and records nothing, because a different answer "
        "would be this API reporting on somebody else's state."
    ),
)
async def unblock_player(
    player_id: UUID,
    user: CurrentUserDep,
    use_case: UnblockPlayerDep,
) -> None:
    await use_case.execute(
        UnblockPlayerCommand(blocker_id=user.id, blocked_id=player_id)
    )


@router.get(
    "",
    response_model=BlockedPlayersResponse,
    response_model_exclude_unset=True,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ErrorResponse,
            "description": (
                "`block_state_unavailable` — your blocks could not be read. Retry "
                "the same request; never draw an empty list for it."
            ),
        },
    },
    summary="Blocked players — the players you blocked",
    description=(
        "**Your own blocks, and nobody else's**: each person you blocked and have "
        "not unblocked, with their name, photograph and when you blocked them, "
        "newest first. Unblock one with `DELETE /blocks/{player_id}`.\n\n"
        "**Nothing here, or anywhere, lists who blocked you.** If somebody you "
        "blocked also blocked you, you see only your own block."
    ),
)
async def read_blocked_players(
    user: CurrentUserDep,
    use_case: ReadBlockedPlayersDep,
) -> BlockedPlayersResponse:
    return BlockedPlayersResponse.of(await use_case.execute(user.id))
