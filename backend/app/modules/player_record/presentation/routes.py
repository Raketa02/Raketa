"""The two record routes: one for a given player, one for the caller.

**The caller's is declared first, so it is never read as an identifier.** Both
sit under ``/players``, and a parameterised segment declared ahead of a literal
one swallows it — ``me`` would be parsed as a player id and answer the one
refusal to everybody. This is the same ordering the profile routes already rely
on, and it is load-bearing rather than tidy.

**Both answer the same shape.** A record is a record whoever is reading it;
``is_self`` is what the client retitles on. There is no second response type and
no second renderer, because two shapes for one sheet is how *How others see you*
and *how a stranger sees you* stop being the same screen.

**No zone differs by more than a title.** What other players said used to —
a figure and a count to a reader, a coarse band to the person it is about — and
since ``docs/adr/0179`` §5 the figure crosses to its subject as to anybody, with
the cost of that written down there rather than here. One response type, one
sportsmanship field, whoever is reading.

**One refusal, and it names nothing** (``docs/adr/0159``). Never disclosed to
you, held, and no such player return the same `404` and the same body, byte for
byte: a payload separating *never disclosed* from *no such player* answers *is
this id real* about a stranger. The client draws one line, and there is nothing
here to draw a second one from.

**A block refuses nothing here, in either direction** (``docs/adr/0193`` §2).
The blocker opens the record to undo the block and reads ``blocked_by_you``; the
blocked person reads the blocker's record byte for byte as before (§3).

**``?sport=`` says what the sheet is about and never who may be seen.** The gates
run in the partition of the **disclosure** — a fact the platform holds — and the
parameter reaches only the resolver that picks which Level is printed. A caller
naming a sport they were never shown this person in changes what is drawn and
nothing about whether it is drawn; a caller naming none gets the subject's most
counted sport, which is the same fallback as naming one they do not play.
"""

from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.core.exception_handlers import ErrorResponse
from app.kernel import Sport
from app.modules.player_record.presentation.dependencies import (
    ReadOwnRecordDep,
    ReadPlayerRecordDep,
)
from app.modules.player_record.presentation.schemas import PlayerRecordResponse
from app.modules.users.presentation.dependencies import CurrentUserDep

router = APIRouter(prefix="/players", tags=["player-record"])

_ONE_REFUSAL: dict[int | str, dict[str, Any]] = {
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponse,
        "description": (
            "`record_unavailable` — **one code for three causes, and the body "
            "is identical in all three.** You were never shown this person; the "
            "account is held or in a state that may not be shown; or there is no "
            "such player. **A block is not one of them**, either way round.\n\n"
            "**The indistinguishability is the feature.** A response that "
            "separated *never disclosed* from *no such player* would answer *is "
            "this id real* about a stranger. Draw one line — *This record isn't "
            "available.* — and do not branch on anything else here, because "
            "there is nothing else here."
        ),
    }
}


SportAsked = Annotated[
    Sport | None,
    Query(
        alias="sport",
        description=(
            "Which sport you arrived from. **It selects what the sheet is "
            "about and never who may be seen.**\n\n"
            "Where the subject holds a rating in it, that is the sport `skill` "
            "is drawn for. Where they do not — and where you send nothing — it "
            "falls back to the sport they have played most, ties broken by the "
            "sport registry's own order. Read `skill.sport` for the answer "
            "rather than assuming it is what you sent.\n\n"
            "Admission is untouched by this. Whether a record opens at all is "
            "decided in the partitions the platform already showed you this "
            "person in, which is not something a client sends."
        ),
    ),
]


@router.get(
    # **Declared before the parameterised route**, or `me` is parsed as a player
    # id and every caller gets the refusal.
    "/me/record",
    response_model=PlayerRecordResponse,
    response_model_exclude_unset=True,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": (
                "`record_unavailable` — this account has no record to draw: not "
                "yet named, or no profile committed. The recovery is onboarding's "
                "second part, which `GET /users/me` already sends a cold launch "
                "into."
            ),
        }
    },
    summary="Your own record — how others see you",
    description=(
        "**The same sheet everybody else is shown about you**, which is what "
        "makes it worth having: the numbers on it have been deciding who you "
        "are offered to since you signed up, and a penalty nobody can look up "
        "is a penalty nobody can fix.\n\n"
        "**Nothing gates it.** The gender preference is mutual and has nothing "
        "to say about somebody reading their own record, and a hold does not "
        "reach it either — this is the one screen a held player has for "
        "finding out how they appear.\n\n"
        "`is_self` is `true`, and `blocked_by_you` is `false`: nobody can block "
        "themselves. Read `is_self` rather than comparing ids.\n\n"
        "**What other players said comes back as the figure and its count** — "
        "`sportsmanship.average` and `sportsmanship.raters`, exactly what a "
        "stranger is served about you. The coarse band that used to stand in "
        "for it here is retired by ADR-0179 §5, which names what that costs. It "
        "changes nothing about how you are matched: Player reliability is "
        "what the reliability filter reads.\n\n"
        "**`?sport=` works here too**, and picks which of your own Levels the "
        "skill card draws — the same resolution a stranger's sheet takes."
    ),
)
async def read_own_record(
    user: CurrentUserDep,
    use_case: ReadOwnRecordDep,
    sport: SportAsked = None,
) -> PlayerRecordResponse:
    return PlayerRecordResponse.of(
        await use_case.execute(reader_id=user.id, arrived_from=sport)
    )


@router.get(
    "/{player_id}/record",
    response_model=PlayerRecordResponse,
    response_model_exclude_unset=True,
    status_code=status.HTTP_200_OK,
    responses=_ONE_REFUSAL,
    summary="One player's record",
    description=(
        "Who this person is, as of the moment you opened it.\n\n"
        "**Read through a prior disclosure, never about a person.** It opens "
        "for somebody you were on a game with, somebody you share a group "
        "with, somebody in a group you run, and yourself — and for nobody "
        "else. Without a rule of that shape this route would be a "
        "player-enumeration endpoint, and a UUID being hard to guess is not an "
        "authorization model.\n\n"
        "**Nothing expires but a group.** A game you were both on discloses "
        "for as long as you are both on it, so a sheet you could open this "
        "morning opens next year. A group opens it while you are both in it, "
        "because its Members lists who is in it now — and while you run a "
        "group they are in.\n\n"
        "**The gates are live.** A hold and an account that may not be shown "
        "are re-evaluated on every open, so a disclosure entitles you to *ask* "
        "and never to be answered.\n\n"
        "**A block is not a gate**, either way round. If you blocked this "
        "person, the record opens and says so — `blocked_by_you` — and offers "
        "the place to unblock. If they blocked you, nothing here differs by a "
        "byte.\n\n"
        "**Asking about yourself is allowed** and answers `is_self: true` — the "
        "client is told rather than left to compare identifiers. It draws the "
        "same sheet `/players/me/record` does, figure for figure: `is_self` "
        "retitles it and moves nothing on it.\n\n"
        "**`?sport=` chooses what the sheet is about, never who may be seen.** "
        "Send the sport you arrived from; where they are not rated in it you "
        "get their most played, and admission is decided from what the platform "
        "already showed you regardless."
    ),
)
async def read_player_record(
    player_id: UUID,
    user: CurrentUserDep,
    use_case: ReadPlayerRecordDep,
    sport: SportAsked = None,
) -> PlayerRecordResponse:
    return PlayerRecordResponse.of(
        await use_case.execute(
            reader_id=user.id, subject_id=player_id, arrived_from=sport
        )
    )
