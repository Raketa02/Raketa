"""The three game routes: read yours, state a score, agree with one.

**There is no route that creates a game.** A game exists because a challenge's
line-up completed, and nothing a client sends can produce one — which is what
makes *these people arranged this* a fact rather than a claim.

**There is no route called confirm.** A result is confirmed when a clock passes,
and a clock is nobody's request. Silence confirming is not an endpoint that goes
missing; it is the absence of one.

**There is no rejection.** Disagreement is a score, always, and the only way to
say *that is not what happened* is to say what did.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, status

from app.core.exception_handlers import ErrorResponse
from app.modules.games.application.commands import (
    AcceptResultCommand,
    StateResultCommand,
)
from app.modules.games.application.read_games import StandingGame
from app.modules.games.domain.game import Game
from app.modules.games.domain.results import Score, SetScore
from app.modules.games.domain.standing import GameStanding
from app.modules.games.domain.windows import (
    acceptance_settles_at,
    entry_closes_at,
    proposal_closes_at,
)
from app.modules.games.presentation.dependencies import (
    AcceptResultDep,
    ReadGamesDep,
    StateResultDep,
)
from app.modules.games.presentation.schemas import (
    GameListResponse,
    GameSchema,
    ScoreSchema,
    SeatingSchema,
    SetScoreSchema,
    StandingProposalSchema,
    StateResultRequest,
)
from app.modules.users.presentation.dependencies import CurrentUserDep

router = APIRouter(prefix="/games", tags=["games"])

#: What both acts refuse, and it is the same list because the refusals are about
#: the game rather than about what was sent.
_REFUSALS: dict[int | str, dict[str, Any]] = {
    status.HTTP_403_FORBIDDEN: {
        "model": ErrorResponse,
        "description": (
            "`you_were_not_on_this_court` — no game of **yours** has that id. "
            "One code for two cases — it does not exist, or you did not play in "
            "it — because separating them would answer *is this id real* about "
            "four strangers' evening."
        ),
    },
    status.HTTP_409_CONFLICT: {
        "model": ErrorResponse,
        "description": (
            "`the_entry_window_has_closed` — nobody said this game happened in "
            "time, so it now reads as never played to everybody who has looked "
            "at it. An entry that resurrected it would contradict a card the "
            "platform has already drawn.\n\n"
            "`the_result_is_settled` — the result is agreed, or the two sides "
            "disagreed and neither answered. **Both are final**: there is no "
            "correction path and no reversal, and reopening a disagreement a day "
            "later is the arbitration this platform refuses."
        ),
    },
}

#: What stating a score refuses on top, and **the acceptance route may not
#: advertise any of it**: it carries no body, so a 400 about a score is a code it
#: cannot return, and a contract that promises one is a client branch that will
#: never be reached.
_STATING_REFUSALS: dict[int | str, dict[str, Any]] = {
    status.HTTP_400_BAD_REQUEST: {
        "model": ErrorResponse,
        "description": (
            "`a_result_must_carry_a_score` — an objection with nothing in it. "
            "There is no bare rejection here: a rejection carrying no score is "
            "free and always optimal for the loser.\n\n"
            "`a_score_must_name_a_winner` — a level set, or a match level in "
            "sets. None of the four sports produces a draw, and *Last 5* has no "
            "third column to put one in.\n\n"
            "`a_score_is_not_this_shape` — more sets than any of these sports "
            "has, or a number no set reaches."
        ),
    },
    status.HTTP_409_CONFLICT: {
        "model": ErrorResponse,
        "description": (
            "Everything above, plus:\n\n"
            "`your_side_has_already_answered` — one score per side. The cap is "
            "what bounds an argument to two rounds, and what makes silence safe "
            "to read as agreement.\n\n"
            "`the_other_side_has_answered` — correcting is free until they "
            "respond and not afterwards."
        ),
    },
}

#: What agreeing refuses on top. Its 409 restates the shared two, because a
#: single response code carries one description and a client reads it whole.
_ACCEPTING_REFUSALS: dict[int | str, dict[str, Any]] = {
    status.HTTP_409_CONFLICT: {
        "model": ErrorResponse,
        "description": (
            "Everything above, plus:\n\n"
            "`nobody_has_proposed_a_result` — there is nothing from the other "
            "side to accept.\n\n"
            "`accepting_your_own_sides_result` — **only the other side can "
            "accept**, because a teammate agreeing with a teammate proves "
            "nothing.\n\n"
            "`the_result_is_already_accepted` — your side has already agreed to "
            "this one."
        ),
    },
}


@router.get(
    "",
    response_model=GameListResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": (
                "Every game you were on the court of, newest arrangement first, "
                "each with what it is right now."
            )
        },
    },
    summary="Your games",
    description=(
        "**Arranged, played and finished in one list.** A game awaiting an "
        "entry, one awaiting an answer and one that never happened are one thing "
        "at three moments of its life.\n\n"
        "**The standing is derived, never stored.** It is folded from the record "
        "and the clock at the moment you asked, so a game whose entry window ran "
        "out reads as never played whether or not anything has swept it — "
        "nothing sweeps it, because there is nothing for a sweep to correct.\n\n"
        "**`read_at` is the instant every standing and deadline here was folded "
        "against.** Render your countdowns from it, so they cannot disagree with "
        "the standing beside them."
    ),
)
async def read_games(
    user: CurrentUserDep,
    use_case: ReadGamesDep,
) -> GameListResponse:
    read_at, found = await use_case.execute(user.id)
    return GameListResponse(
        read_at=read_at,
        games=[_game(one, reader_id=user.id) for one in found],
    )


@router.post(
    "/{game_id}/result",
    response_model=GameSchema,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "The game as it stands with your score on the table."
        },
        **_REFUSALS,
        **_STATING_REFUSALS,
    },
    summary="State the result",
    description=(
        "**One act, and the record decides what it means.** Send the score you "
        "believe was played:\n\n"
        "- nothing on the table yet → you are saying *we played, here is the "
        "score*, and **that entry is what records that the game happened**. "
        "There is no date to send: the moment of the entry is the moment.\n"
        "- your own side's score on the table, unanswered → a **correction**, "
        "free, and not a second turn. Any of your side may make it, not only "
        "whoever typed first.\n"
        "- the other side's score on the table → your side's **one** "
        "disagreement, and it carries a score because there is no bare "
        "rejection.\n\n"
        "**A lone score is confirmed by silence** when its 24 hours run out, and "
        "the game counts. **Two scores nobody accepts leave the game unscored** "
        "— which still counts as an evening you played and moves nobody's "
        "Level.\n\n"
        "**Nobody is penalised for any of this.** Not for saying nothing, not "
        "for disagreeing, not for a disagreement the other side ignored."
    ),
)
async def state_result(
    game_id: UUID,
    payload: StateResultRequest,
    user: CurrentUserDep,
    use_case: StateResultDep,
) -> GameSchema:
    return _game(
        await use_case.execute(
            StateResultCommand(
                game_id=game_id,
                player_id=user.id,
                score=_score(payload.score),
            )
        ),
        reader_id=user.id,
    )


@router.post(
    "/{game_id}/result/acceptance",
    response_model=GameSchema,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "The game as it stands with your agreement recorded."
        },
        **_REFUSALS,
        **_ACCEPTING_REFUSALS,
    },
    summary="Agree with the result",
    description=(
        "**One opponent suffices.** The person across the net is the whole of "
        "the evidence that a score was real.\n\n"
        "**It does not settle the result immediately.** The grace runs from the "
        "*score*, not from your tap, and inside it a disagreement still wins — "
        "so a partner who is quick to their phone cannot close the door on an "
        "opponent who has not read it yet. `standing_proposal.settles_at` is "
        "when it becomes final.\n\n"
        "**Saying nothing does the same thing**, a day later. Accepting is how "
        "you make it true sooner, and it is never how you avoid a penalty — "
        "there is none."
    ),
)
async def accept_result(
    game_id: UUID,
    user: CurrentUserDep,
    use_case: AcceptResultDep,
) -> GameSchema:
    return _game(
        await use_case.execute(
            AcceptResultCommand(game_id=game_id, player_id=user.id)
        ),
        reader_id=user.id,
    )


def _score(payload: ScoreSchema) -> Score:
    """The wire's sets as the domain's score. **Validated there, not here.**

    Pydantic bounds the shape — how many sets, and the range of a number in one —
    and the value object holds the rules: a level set has not finished, and a
    score names a winner. A route that duplicated either would be a second place
    for them to be true.
    """

    return Score.of(SetScore(a=one.a, b=one.b) for one in payload.sets)


def _game(one: StandingGame, *, reader_id: UUID) -> GameSchema:
    """One game as its own court is allowed to see it.

    The occupants are bare ids, for the reason a challenge's are: a card, a Level
    and an area belong to a search's answer, where a gate decided they may be
    shown. A game is a record of an evening, and a screen that re-published
    somebody's profile off the back of it would be a directory with extra steps.
    """

    game: Game = one.game
    now = one.read_at
    proposal = game.standing_proposal()
    return GameSchema(
        game_id=game.id,
        challenge_id=game.challenge_id,
        sport=game.sport,
        kind=game.kind,
        window=game.window,
        standing=one.standing,
        planned_at=game.planned_at,
        played_at=game.played_at,
        entry_closes_at=(
            entry_closes_at(game.planned_at) if game.played_at is None else None
        ),
        seats=[
            SeatingSchema(side=seating.side, player_id=seating.player_id)
            for seating in game.line_up.seatings
        ],
        score=_rendered(game.confirmed_score_at(now)),
        outcome=game.outcome_for(reader_id, now=now),
        standing_proposal=(
            None
            if proposal is None or one.standing is not GameStanding.AWAITING_ANSWER
            else StandingProposalSchema(
                side=proposal.side,
                proposed_by=proposal.by,
                score=_rendered(proposal.score),
                proposed_at=proposal.at,
                answer_by=proposal_closes_at(proposal.at),
                settles_at=acceptance_settles_at(proposal.at),
            )
        ),
    )


def _rendered(score: Score | None) -> ScoreSchema | None:
    if score is None:
        return None
    return ScoreSchema(
        sets=[SetScoreSchema(a=one.a, b=one.b) for one in score.sets]
    )
