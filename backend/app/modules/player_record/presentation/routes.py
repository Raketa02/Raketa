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

**One refusal, and it names nothing** (``docs/adr/0155``). Never disclosed to
you, blocked either way, held, and no such player return the same `404` and the
same body, byte for byte. A payload naming the gate delivers a block to the one
person the block was meant to be invisible to; a payload separating *never
disclosed* from *no such player* answers *is this id real* about a stranger. The
client draws one line, and there is nothing here to draw a second one from.

**There is no ``?sport=`` on either route yet.** The reader's arrival sport
selects which sport the sheet is *about* and never who may be seen — the gates
run in the partition of the **disclosure**, which is a fact the platform holds
rather than one the client sends. Nothing on this response is per sport today, so
the parameter arrives with the skill card that needs it.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, status

from app.core.exception_handlers import ErrorResponse
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
            "`record_unavailable` — **one code for four causes, and the body is "
            "identical in all four.** You were never shown this person; one of "
            "you has blocked the other; the account is held or in a state that "
            "may not be shown; or there is no such player.\n\n"
            "**The indistinguishability is the feature.** A response that named "
            "which would deliver a block to the one person a block is meant to "
            "be invisible to, and a response that separated *never disclosed* "
            "from *no such player* would answer *is this id real* about a "
            "stranger. Draw one line — *This record isn't available.* — and do "
            "not branch on anything else here, because there is nothing else "
            "here."
        ),
    }
}


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
                "`record_unavailable` — this account has no record to draw: no "
                "handle, or no profile committed. The recovery is onboarding's "
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
        "**Nothing gates it.** A block is between two people and the gender "
        "preference is mutual; neither has anything to say about somebody "
        "reading their own record, and a hold does not reach it either — this "
        "is the one screen a held player has for finding out how they appear.\n\n"
        "`is_self` is `true`. Read it rather than comparing ids."
    ),
)
async def read_own_record(
    user: CurrentUserDep,
    use_case: ReadOwnRecordDep,
) -> PlayerRecordResponse:
    return PlayerRecordResponse.of(await use_case.execute(reader_id=user.id))


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
        "for somebody a search of yours returned, somebody you share a live "
        "challenge or a game with, and yourself — and for nobody else. Without "
        "a rule of that shape this route would be a player-enumeration "
        "endpoint, and a UUID being hard to guess is not an authorization "
        "model.\n\n"
        "**Nothing expires.** A search record is kept for ever, so a sheet you "
        "could open this morning opens next year — any shorter window could "
        "only refuse a face the app is currently showing.\n\n"
        "**The gates are live.** A block placed since the search, a hold, an "
        "account that may not be shown and the mutual gender preference are "
        "re-evaluated on every open, so a disclosure entitles you to *ask* and "
        "never to be answered.\n\n"
        "**Asking about yourself is allowed** and answers `is_self: true` — the "
        "client is told rather than left to compare identifiers."
    ),
)
async def read_player_record(
    player_id: UUID,
    user: CurrentUserDep,
    use_case: ReadPlayerRecordDep,
) -> PlayerRecordResponse:
    return PlayerRecordResponse.of(
        await use_case.execute(reader_id=user.id, subject_id=player_id)
    )
