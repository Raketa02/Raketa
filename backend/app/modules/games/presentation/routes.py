"""The six game routes: read yours, read one's pairing, state a score, agree
with one — and, on a booked game, say somebody did not come, or say you did
(#547).

**There is no route that creates a game, none that moves a seat on one, and
none that ends one.** A game exists because a booking opened it (#541), and
nothing a client sends here can produce one — which is what makes *these people
arranged this* a fact rather than a claim. A seat opens because somebody left
the **booking** and is filled by a rescue (#544, #545); here a seat somebody
left is drawn with `player_id: null` (``docs/adr/0162``). And a game is
**called off** because its booking was — at the club's cut-off with a seat
open, or by the club — which is where the act's permission lives; here it is
read as `standing: CALLED_OFF` with `called_off_at` beside it
(``docs/adr/0163``, ``docs/adr/0172`` §4).

**The pairing is read beside the game and never on it** (``docs/adr/0161``).
``GameSchema`` carries no forecast and never will; what the game screen draws
is computed when asked, for the reader, for as long as the game has not
happened — and the seat on the list still carries a name and nothing else.

**There is no route called confirm.** A result is settled by silence when a clock
passes, and a clock is nobody's request — or at once by *That's right* from across
the net, which is the acceptance (#654). Silence settling is not an endpoint that
goes missing; it is the absence of one.

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
    DisputeANoShowCommand,
    ReportANoShowCommand,
    StateResultCommand,
)
from app.modules.games.application.read_game_pairing import GamePairingRead
from app.modules.games.presentation.dependencies import (
    AcceptResultDep,
    DisputeANoShowDep,
    ReportANoShowDep,
    ReadGamePairingDep,
    ReadGamesDep,
    StateResultDep,
)
from app.modules.games.presentation.schemas import (
    GameListResponse,
    GamePairingResponse,
    GameSchema,
    ReportANoShowRequest,
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
            "`the_result_is_settled` — the result is final: agreed with, settled "
            "by silence, settled with the closer of two scores naming the same "
            "winner, or **disputed** — two scores naming different winners. "
            "There is no correction path and no reversal, and reopening a "
            "disagreement a day later is the arbitration this platform refuses."
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
            "`the_game_has_not_started` — no score is taken before the game's "
            "hour: nothing can have happened yet.\n\n"
            "`your_side_has_already_answered` — one score per side. The cap is "
            "what bounds an argument to two rounds, and what makes silence safe "
            "to read as agreement. A correction after the other side has put "
            "its own score up is the same refusal.\n\n"
            "`corrections_have_closed` — the entry window has closed (24 hours "
            "after the hour ended), and with it the time to correct your side's "
            "score. It still stands, and its answer window still runs.\n\n"
            "`the_court_has_an_open_seat` — somebody left and nobody has filled "
            "their seat, so there is no court to have played on. Fill it, or "
            "let the window close.\n\n"
            "`the_game_was_called_off` — somebody ended it while a seat was "
            "open, so there is nothing to have played. The ending is on "
            "`standing` and `called_off_at`.\n\n"
            "`the_game_started_short` — a booked game whose hour came with a "
            "seat open: somebody left after the club's cut-off and nobody took "
            "the seat. It ends uncounted (`standing` `STARTED_SHORT`), and "
            "nothing about it can be recorded.\n\n"
            "`a_no_show_is_reported` — somebody was reported as not coming to "
            "this booked game and their day to dispute it runs (`no_shows`): "
            "the game does not count, so there is no score to enter."
        ),
    },
}

#: What reporting somebody who did not come refuses (#547).
_REPORTING_REFUSALS: dict[int | str, dict[str, Any]] = {
    status.HTTP_400_BAD_REQUEST: {
        "model": ErrorResponse,
        "description": (
            "`not_on_this_court` — that player was not on this game.\n\n"
            "`you_cannot_report_yourself` — you are the one person your report "
            "proves came."
        ),
    },
    status.HTTP_409_CONFLICT: {
        "model": ErrorResponse,
        "description": (
            "Everything above, plus:\n\n"
            "`no_shows_are_for_booked_games` — only a game booked on a court "
            "has an hour somebody could fail to come to.\n\n"
            "`the_game_has_not_started` — its hour has not come yet.\n\n"
            "`a_result_is_entered` — somebody already said you played, with a "
            "score; answer the score instead.\n\n"
            "`you_were_reported_as_a_no_show` — you were reported yourself; "
            "dispute it instead.\n\n"
            "`the_game_was_called_off`, `the_game_started_short` — there was no "
            "game to come to."
        ),
    },
}

#: What disputing a report refuses (#547).
_DISPUTING_REFUSALS: dict[int | str, dict[str, Any]] = {
    status.HTTP_403_FORBIDDEN: _REFUSALS[status.HTTP_403_FORBIDDEN],
    status.HTTP_409_CONFLICT: {
        "model": ErrorResponse,
        "description": (
            "`nobody_reported_you` — there is nothing of yours to dispute.\n\n"
            "`the_dispute_window_has_closed` — your day to say you came has "
            "passed: the report stands."
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
            "nothing."
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
        games=[GameSchema.of(one, reader_id=user.id) for one in found],
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
        "`GET /games` changes: a seat there still carries a name and nothing "
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
        "**No score is taken before the game's hour**, and a correction is "
        "refused once the entry window has closed.\n\n"
        "**A lone score is settled by silence** when its 24 hours "
        "(`proposals[].answer_by`) run out, and the game counts. **Two scores "
        "nobody agrees with settle when the later one's 24 hours run out**: "
        "naming the same winner, the game counts with the **closer** score — "
        "the smaller margin in games, and on a tie the first put up; naming "
        "different winners, it ends `DISPUTED` and moves nobody's Level.\n\n"
        "**A For fun game asks nobody**: its score is the result the moment it "
        "is put up (`CONFIRMED`), with no answer window, and no Level moves."
    ),
)
async def state_result(
    game_id: UUID,
    payload: StateResultRequest,
    user: CurrentUserDep,
    use_case: StateResultDep,
) -> GameSchema:
    return GameSchema.of(
        await use_case.execute(
            StateResultCommand(
                game_id=game_id,
                player_id=user.id,
                score=payload.score.as_score(),
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
        "***That's right.*** **One opponent suffices**: the person across the "
        "net is the whole of the evidence that a score was real.\n\n"
        "**It settles the result at once and closes the game** (`standing` "
        "`CONFIRMED`, the agreed score on `score`). No different score is "
        "taken after it, so in doubles the first agreement from the other "
        "side is the one that counts. On a Competitive game the Levels move "
        "within a minute.\n\n"
        "**Saying nothing settles it too**, once the score's 24 hours "
        "(`proposals[].answer_by`) run out."
    ),
)
async def accept_result(
    game_id: UUID,
    user: CurrentUserDep,
    use_case: AcceptResultDep,
) -> GameSchema:
    return GameSchema.of(
        await use_case.execute(AcceptResultCommand(game_id=game_id, player_id=user.id)),
        reader_id=user.id,
    )


@router.post(
    "/{game_id}/no-shows",
    response_model=GameSchema,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "The game as it stands with your report on it."
        },
        **_REFUSALS,
        **_REPORTING_REFUSALS,
    },
    summary="Say somebody didn't come",
    description=(
        "***Kuba didn't come*** — on a **booked** game whose hour has come, "
        "where you would otherwise enter the result (#547). Said by somebody "
        "who came, about somebody else on the court; a second report of the "
        "same player answers the same and writes nothing, and each player "
        "who did not come is reported on their own.\n\n"
        "**The game does not count** from the report on, and nobody's Level "
        "moves. The reported player has **24 hours to dispute it** "
        "(`no_shows[].dispute_by`); after that it stands — the strongest mark "
        "on a record — with nothing written at that moment. **Nobody "
        "arbitrates a dispute**: the report falls and is on nobody's record."
    ),
)
async def report_a_no_show(
    game_id: UUID,
    payload: ReportANoShowRequest,
    user: CurrentUserDep,
    use_case: ReportANoShowDep,
) -> GameSchema:
    return GameSchema.of(
        await use_case.execute(
            ReportANoShowCommand(
                game_id=game_id, player_id=user.id, absent_id=payload.player_id
            )
        ),
        reader_id=user.id,
    )


@router.post(
    "/{game_id}/no-shows/dispute",
    response_model=GameSchema,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "The game as it stands with your dispute recorded."
        },
        **_DISPUTING_REFUSALS,
    },
    summary="Say you came",
    description=(
        "**You were reported as not coming, and you did** (#547). Inside 24 "
        "hours of the report. The report falls, nothing goes on your record, "
        "and the game still does not count: nobody arbitrates which of you is "
        "right. A second dispute answers the same and writes nothing."
    ),
)
async def dispute_a_no_show(
    game_id: UUID,
    user: CurrentUserDep,
    use_case: DisputeANoShowDep,
) -> GameSchema:
    return GameSchema.of(
        await use_case.execute(
            DisputeANoShowCommand(game_id=game_id, player_id=user.id)
        ),
        reader_id=user.id,
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
