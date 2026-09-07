"""The two block endpoints: make one, lift one. **Nothing reads one back.**

The eight-route table in the matchmaking spec has no block route on it while its
user stories 49–53 require a player to be able to block, so these two are added
on that reading: a control the client cannot reach is not a control. They are
flat-prefixed like every other router in this backend, with no context segment.

**Both answer 204, always, and the body is empty because there is nothing that
may be in it.** Blocking somebody already blocked, unblocking somebody who was
never blocked, blocking an id that belongs to nobody — all three answer exactly
as the ordinary case does. That is not laziness about status codes: a distinct
answer for any of them is the response shape reporting on state, and *no response
anywhere reveals a block* (``docs/adr/0095`` §8) is the promise that makes the
control usable rather than confrontational.

**The blocked party is never told, and there is no route through which they
could be.** There is no list endpoint here, in either direction. A player's own
list of people they have blocked is a legitimate screen and is not this ticket's;
when it arrives it serves the caller's *own* blocks and nothing else.

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
    UnblockPlayerDep,
)
from app.modules.blocks.presentation.schemas import BlockPlayerRequest
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
        "The two of you disappear from each other's view everywhere, "
        "immediately, silently, in **both** directions.\n\n"
        "**Idempotent.** Blocking somebody already blocked records nothing and "
        "answers 204.\n\n"
        "**No cap, no cooldown and no rate limit**, and none will be added.\n\n"
        "**There is no reason field.** A reason belongs to a report, and this is "
        "not one.\n\n"
        "**Neither side is notified**, in either direction, and no response in "
        "this API reveals a block to the blocked party.\n\n"
        "**The record is directed and the effect is symmetric.** Your block of "
        "them and their block of you are independent: lifting yours never lifts "
        "theirs, and neither of you can discover which way one went.\n\n"
        "**It is forward-looking.** It removes each of you from the other's "
        "future listings; it does not reach into anything already agreed."
    ),
)
async def block_player(
    payload: BlockPlayerRequest,
    user: CurrentUserDep,
    use_case: BlockPlayerDep,
) -> None:
    await use_case.execute(
        BlockPlayerCommand(
            blocker_id=user.id,
            blocked_id=payload.player_id,
            surface=payload.surface,
        )
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
        "Lifts **your** block of this player, immediately.\n\n"
        "**It lifts one direction.** If they have also blocked you, that block "
        "stands and the two of you stay invisible to each other — and nothing "
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
