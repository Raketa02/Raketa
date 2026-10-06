"""The Play intent declaration: ADR-0094's write path, unkeyed.

**The route is top-level and not under `/players/me`.** The declaration is not on
the profile — that is the whole of ADR-0094, which put it in its own aggregate
keyed `(player, sport)` so that a sport rated after onboarding can still acquire
an intent — and moving a shipped record's route to make two URLs rhyme would be
the shape of the aggregate following the shape of the URL.

**The sport is the path, because it is half the resource's identity.** The
resource is one player's intent in one sport; the player is the token.

**Unkeyed, and there is nothing here to deduplicate.** The same request twice
lands the same state, and the aggregate's no-op rule means the second appends
nothing — including one that arrives from a different screen, because *the same
answer, given again, from a different surface* is a fact about where somebody was
standing rather than about what kind of game they want.

**Three surfaces reach this route**, and each says which it was: the rating
tail (the required first declaration), the search screen's inline offer when a
player switches the mode toggle away from what they declared, and the daily drift
prompt's backstop. A settings screen is deliberately not one of them.
"""

from __future__ import annotations

from fastapi import APIRouter, Path, status

from app.core.exception_handlers import ErrorResponse
from app.kernel import Sport
from app.modules.player_profile.application.commands import (
    DeclarePlayIntentCommand,
)
from app.modules.player_profile.presentation.dependencies import (
    DeclarePlayIntentDep,
)
from app.modules.player_profile.presentation.schemas import (
    DeclarePlayIntentRequest,
    PlayIntentDeclarationResponse,
)
from app.modules.users.presentation.dependencies import CurrentUserDep

router = APIRouter(prefix="/play-intents", tags=["player-profile"])


@router.put(
    "/{sport}",
    response_model=PlayIntentDeclarationResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": (
                "`concurrent_modification` — two declarations for this player "
                "in this sport raced and this one lost. Retry: the retry reads "
                "the winner and either changes it or is a no-op."
            ),
        },
    },
    summary="Declare what kind of game this player wants, in one sport",
    description=(
        "Unkeyed and idempotent. The same value twice lands the same state and "
        "records nothing the second time — intent is a **preference, not a "
        "consent**: there is no wording to evidence it against, so a stream that "
        "grew an event for an unchanged answer would be recording that a player "
        "did not do anything.\n\n"
        "**There is no null and no unanswered state.** `NO_PREFERENCE` is an "
        "explicit answer — *either kind of evening suits me* — and the matcher "
        "must be able to tell it from *I never opened that screen*, which is "
        "what an absent declaration means. Nobody is ever backfilled to it.\n\n"
        "**A declaration is not a game's kind.** A game is counted or for "
        "fun; intent is what you told the platform about this sport and has "
        "three values — this route is what *make this my intent* means.\n\n"
        "**It needs no profile.** Intent is asked for at the tail of a rating "
        "run, which happens before onboarding's second part, so a declaration "
        "with no profile behind it is the ordinary first case."
    ),
)
async def declare_play_intent(
    payload: DeclarePlayIntentRequest,
    user: CurrentUserDep,
    use_case: DeclarePlayIntentDep,
    sport: Sport = Path(
        ...,
        description=(
            "The sport this declaration is about. Intent is per sport and never "
            "transfers between them — no object in the system holds two sports' "
            "intent at once."
        ),
    ),
) -> PlayIntentDeclarationResponse:
    declaration = await use_case.execute(
        DeclarePlayIntentCommand(
            player_id=user.id,
            sport=sport,
            intent=payload.intent,
            surface=payload.surface,
        )
    )
    return PlayIntentDeclarationResponse.from_domain(declaration)
