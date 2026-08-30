"""*Not now* — the answer to a prompt that writes no value.

**A top-level resource, and write-only.** Every other answer to a prompt is a
write through the route that owns the value — the radius, the week, the
declaration — and needs nothing from this context. This is the one answer that
changes nothing anywhere, which is exactly why it has to be recorded: of a
prompt's three outcomes, *raised* and *accepted* are both recomputable from rows
that already exist, and *declined* is nowhere.

**Nothing is returned by this route, and no route anywhere returns a decline.**
Not to the player, not as a count, not as a timestamp — so it answers `204` and
not a body.

**It retires nothing.** The standing question is left to expire on its own; what
a decline buys is that the next search does not raise it again. A caller still
cannot make a question quietly stop being asked.

**No Origin key**, unlike the pass beside it. That one was bought for a named
falsifier; nothing here demands one, and two of the three questions this route
answers are raised by a background loop with no search to cite.
"""

from __future__ import annotations

from fastapi import APIRouter, Response, status

from app.core.exception_handlers import ErrorResponse
from app.modules.matchmaking.application.commands import RecordPromptDeclineCommand
from app.modules.matchmaking.presentation.dependencies import (
    RecordPromptDeclineDep,
)
from app.modules.matchmaking.presentation.schemas import RecordPromptDeclineRequest
from app.modules.users.presentation.dependencies import CurrentUserDep

router = APIRouter(prefix="/prompt-declines", tags=["prompt-declines"])


@router.post(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": (
                "Recorded. **Nothing is returned** — there is no route through "
                "which a decline reaches anybody, including you."
            ),
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": (
                "`prompt_does_not_suppress` — *Keep these times?* is asked "
                "again on the next search, because the week you improvised is a "
                "different week next Tuesday. It is the one prompt with no "
                "*not now*."
            ),
        },
    },
    summary="Not now",
    description=(
        "Stops a question being raised at you again for a while, and reaches "
        "nothing else.\n\n"
        "**It changes no value.** Saying *yes* to one of these is a `PUT` "
        "through the route that owns the value — your radius, your week, your "
        "play intent — and this is what the other button does.\n\n"
        "**It retires nothing**, including itself: the question standing right "
        "now still expires on its own, and this is about the next time it would "
        "have been asked.\n\n"
        "**It is keyed by the question and never by the value quoted at you.** "
        "Declining *keep 22 km?* also answers *keep 32 km?* — you answered "
        "about a habit, not about a number. Which sport it goes quiet for "
        "depends on the question: a play intent is declared per sport, while "
        "your radius and your week are one fact each.\n\n"
        "**There is no `search_id`** and no window to name."
    ),
)
async def decline_a_prompt(
    payload: RecordPromptDeclineRequest,
    user: CurrentUserDep,
    use_case: RecordPromptDeclineDep,
) -> Response:
    await use_case.execute(
        RecordPromptDeclineCommand(
            player_id=user.id,
            prompt=payload.prompt,
            sport=payload.sport,
        )
    )
    # Built here rather than returned as `None`, so the route's declared `204`
    # and what it actually sends cannot come apart: there is no body, and there
    # is no shape a body could be.
    return Response(status_code=status.HTTP_204_NO_CONTENT)
