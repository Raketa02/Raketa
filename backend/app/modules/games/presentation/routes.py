"""The four game routes: read yours, read one's pairing, state a score, agree
with one.

**There is no route that creates a game, and none that moves a seat on one.** A
game exists because a challenge's line-up completed, and nothing a client sends
can produce one — which is what makes *these people arranged this* a fact rather
than a claim. A seat opens because somebody left the **challenge**
(``POST /challenges/{id}/departure``) and is filled because the next completed
line-up re-seated the same game; here a seat somebody left is drawn with
`player_id: null` (``docs/adr/0162``).

**The pairing is read beside the game and never on it** (``docs/adr/0161``).
``GameSchema`` carries no forecast and never will; what the game screen draws
is computed when asked, for the reader, for as long as the game has not
happened — and the seat on the list still carries a handle and nothing else.

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
from app.modules.games.application.read_game_pairing import GamePairingRead
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
    ReadGamePairingDep,
    ReadGamesDep,
    StateResultDep,
)
from app.modules.games.presentation.schemas import (
    AcceptanceSchema,
    GameListResponse,
    GamePairingResponse,
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
            "respond and not afterwards. `acceptance.agreed_at` is when they "
            "did, so the sentence a player reads need not be vague about it.\n\n"
            "`the_court_has_an_open_seat` — somebody left and nobody has filled "
            "their seat, so there is no court to have played on. Fill it, or "
            "let the window close."
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


@router.get(
    "/{game_id}/pairing",
    response_model=GamePairingResponse,
    response_model_exclude_unset=True,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": (
                "What this platform makes of your court, computed for you at "
                "`read_at`."
            )
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": (
                "`game_not_found` — no game of **yours** has that id. One code "
                "for two cases — it does not exist, or you were not on its "
                "court — because separating them would answer *is this id "
                "real* about four strangers' evening."
            ),
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": (
                "`pairing_is_history` — the game has happened, or its entry "
                "window closed on silence. The pairing means what a card means "
                "*because this game has not happened*; afterwards the values "
                "would be a claim about people made from a record that has "
                "moved on."
            ),
        },
    },
    summary="The game's pairing",
    description=(
        "**The game screen's forecast, split, stakes and Levels, computed when "
        "you ask.** Nothing here is stored on the game, and nothing on "
        "`GET /games` changes: a seat there still carries a handle and nothing "
        "else.\n\n"
        "**Read in your direction.** `split.gap` is your side's strength minus "
        "theirs, and `at_stake` is what a counted result would do to *your* "
        "Level — the rating engine's own rule read forward, side against side, "
        "so it is the pair the result will deliver.\n\n"
        "**Three blocks, each omitted on its own ground.** `forecast` and "
        "`split` are omitted together when the pairing cannot be computed — "
        "somebody on the court holds no rating in the sport, or a seat could "
        "not be priced — and there is deliberately no reason beside the "
        "absence. `at_stake` is omitted on a friendly, where a counted result "
        "is meaningless rather than unavailable, and where the rule has nothing "
        "to move or nothing to price against — you hold no rating in the sport, "
        "or nobody across the net does. `seats` names the Level of everybody "
        "the platform holds one for.\n\n"
        "**Only while the game is awaiting an entry.** After *we played* — or "
        "after the entry window closed on silence — the route refuses, because "
        "a pairing is a claim about a game that has not happened."
    ),
)
async def read_game_pairing(
    game_id: UUID,
    user: CurrentUserDep,
    use_case: ReadGamePairingDep,
) -> GamePairingResponse:
    return _pairing(await use_case.execute(game_id, user.id))


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
        "opponent who has not read it yet. `acceptance.settles_at` is when it "
        "becomes final, and it is on the response the **proposing** side reads "
        "too — a score that has been agreed is no longer a score waiting on "
        "silence.\n\n"
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

    The occupants carry **a handle and nothing else** (``docs/adr/0141``). A
    card, a Level and an area belong to a search's answer, where a gate decided
    they may be shown; a game is a record of an evening, and a screen that
    re-published somebody's profile off the back of it would be a directory with
    extra steps. A handle is not that: it is what these four people already knew
    about each other by the time they were on a court together, and without it
    the screens name *sides* — which leaves a result agreed with nobody and three
    padel games in a week told apart by nothing but how long ago they were
    arranged.

    **Nothing here is re-gated against who is reading.** The four fail-closed
    gates decide who may be *introduced*, and an evening you were both at is not
    an introduction; ``docs/adr/0095`` §7 already settled that a block is
    forward-looking and does not reach into a game already agreed. A handle that
    vanished from a row would also be the trace §8 says neither party ever sees.
    """

    game: Game = one.game
    now = one.read_at
    # **The argument travels only while it is one.** Before an entry there is
    # nothing on the table, and after an ending the ending is the answer: a
    # confirmed score is ``score``, and an unscored game is an evening rather
    # than a transcript of what was said about it.
    arguing = one.standing is GameStanding.AWAITING_ANSWER
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
            SeatingSchema(
                side=seating.side,
                player_id=seating.player_id,
                nickname=(
                    None
                    if seating.player_id is None
                    else one.handles.get(seating.player_id)
                ),
            )
            for seating in game.line_up.seatings
        ],
        score=_rendered(game.confirmed_score_at(now)),
        outcome=game.outcome_for(reader_id, now=now),
        proposals=[
            StandingProposalSchema(
                side=proposal.side,
                proposed_by=proposal.by,
                score=_rendered(proposal.score),
                proposed_at=proposal.at,
                answer_by=proposal_closes_at(proposal.at),
                settles_at=acceptance_settles_at(proposal.at),
            )
            for proposal in (game.standing_proposals() if arguing else ())
        ],
        acceptance=_agreement(game) if arguing else None,
    )


def _pairing(one: GamePairingRead) -> GamePairingResponse:
    """The port's answer as the wire carries it, and **no arithmetic**.

    Built through ``model_validate`` over a dict rather than by keyword, because
    the route is declared ``response_model_exclude_unset=True`` and an absent
    block has to stay absent: a key that is not here generates as ``field?: T``
    and is not in the JSON at all. Every number crosses as the engine produced
    it; ``gap`` is the split's own property and never a subtraction done here.

    A pairing the port could not read at all — ``None`` — draws exactly what a
    pairing with nothing in it draws: nothing, with the seats empty. The wire
    does not tell the two apart, by decision (``docs/adr/0161`` §4).
    """

    pairing = one.pairing
    fields: dict[str, Any] = {"read_at": one.read_at, "seats": []}
    if pairing is None:
        return GamePairingResponse.model_validate(fields)
    fields["seats"] = [
        {
            "player_id": seat.player_id,
            "level": seat.level,
            "band": seat.band,
            "range": {"low": seat.range_low, "high": seat.range_high},
            "confidence": seat.confidence,
        }
        for seat in pairing.seats
    ]
    if pairing.forecast is not None and pairing.split is not None:
        fields["forecast"] = {
            "pct": pairing.forecast.pct,
            "sigma_group": pairing.forecast.sigma_group,
            "provisional": pairing.forecast.provisional,
            "assumption": pairing.forecast.assumption,
        }
        fields["split"] = {
            "your_side": pairing.split.your_side,
            "their_side": pairing.split.their_side,
            "gap": pairing.split.gap,
        }
    if pairing.at_stake is not None:
        fields["at_stake"] = {
            "win_delta": pairing.at_stake.win_delta,
            "loss_delta": pairing.at_stake.loss_delta,
        }
    return GamePairingResponse.model_validate(fields)


def _agreement(game: Game) -> AcceptanceSchema | None:
    """The agreement waiting out its grace, and ``None`` when none is.

    The two readers are asked together because the moment is dated from the
    **score** and never from the tap: an agreement and the proposal it settles
    are one answer, and the aggregate returns them ``None`` together.
    """

    acceptance = game.standing_acceptance()
    accepted = game.accepted_proposal()
    if acceptance is None or accepted is None:
        return None
    return AcceptanceSchema(
        agreed_by=acceptance.by,
        of_side=acceptance.of_side,
        agreed_at=acceptance.at,
        settles_at=acceptance_settles_at(accepted.at),
    )


def _rendered(score: Score | None) -> ScoreSchema | None:
    if score is None:
        return None
    return ScoreSchema(
        sets=[SetScoreSchema(a=one.a, b=one.b) for one in score.sets]
    )
