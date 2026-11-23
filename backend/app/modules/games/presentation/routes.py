"""The eight game routes: read yours, read one's pairing, state a score, agree
with one — and, on a booked game, say who isn't here yet, who has arrived, that
you were there after all, and that somebody was (#657).

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
    ClaimPresenceCommand,
    ConfirmPresenceCommand,
    NoteAbsentCommand,
    NoteArrivalCommand,
    StateResultCommand,
)
from app.modules.games.application.read_game_pairing import GamePairingRead
from app.modules.games.presentation.dependencies import (
    AcceptResultDep,
    ClaimPresenceDep,
    ConfirmPresenceDep,
    NoteAbsentDep,
    NoteArrivalDep,
    ReadGamePairingDep,
    ReadGamesDep,
    StateResultDep,
)
from app.modules.games.presentation.schemas import (
    ArrivalRequest,
    GameListResponse,
    GamePairingResponse,
    GameSchema,
    NotHereYetRequest,
    PresenceConfirmationRequest,
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
            "`the_entry_window_has_closed` — nobody recorded this game in time, "
            "so it now reads `PLAYED_NO_SCORE` to everybody who has looked at "
            "it. A score that arrived now would contradict a card the platform "
            "has already drawn.\n\n"
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
            "`somebody_is_not_here_yet` — somebody was tapped *isn't here yet* "
            "and is still awaited (`attendance`): the score waits until they "
            "arrive or the first 30 minutes are over.\n\n"
            "`somebody_did_not_come` — somebody Didn't come (`attendance`): the "
            "game takes no score and never counts, unless their *I was there* "
            "is confirmed."
        ),
    },
}

#: What a tap in the tap window refuses (#657). **Every refusal is a plain
#: sentence** on `message`.
_AT_THE_COURT_REFUSALS: dict[int | str, dict[str, Any]] = {
    status.HTTP_400_BAD_REQUEST: {
        "model": ErrorResponse,
        "description": (
            "`not_on_this_court` — that player isn't on this game.\n\n"
            "`not_about_yourself` — *isn't here yet* is never said of yourself: "
            "the tap is the proof that you are."
        ),
    },
    status.HTTP_403_FORBIDDEN: _REFUSALS[status.HTTP_403_FORBIDDEN],
    status.HTTP_409_CONFLICT: {
        "model": ErrorResponse,
        "description": (
            "`not_at_the_club` — the fix sent with the tap is not within 300 m "
            "of the club's map point, allowing for its own accuracy up to "
            "200 m: *You can say so only from Ogrody 33.*\n\n"
            "`the_game_has_not_started`, `the_tap_window_has_closed` — a tap "
            "is taken from the game's start until 30 minutes after it, and "
            "never outside.\n\n"
            "`already_arrived` — their arrival is already noted; the first one "
            "counts.\n\n"
            "`you_are_not_here_yourself` — you are tapped and awaited yourself, "
            "so you can't say who else is here.\n\n"
            "`nobody_said_they_were_not_here` — an arrival of somebody nobody "
            "tapped: everybody who arrives on time does nothing.\n\n"
            "`the_result_is_settled` — the result is already final. A score "
            "still waiting for its answer stops no tap: it waits with the "
            "game, and counts for nothing if somebody never comes.\n\n"
            "`attendance_is_for_booked_games`, `the_game_was_called_off`, "
            "`the_game_started_short` — there was no game to come to."
        ),
    },
}

#: What the late claim and its confirmation refuse (#657).
_LATE_CLAIM_REFUSALS: dict[int | str, dict[str, Any]] = {
    status.HTTP_400_BAD_REQUEST: _AT_THE_COURT_REFUSALS[status.HTTP_400_BAD_REQUEST],
    status.HTTP_403_FORBIDDEN: _REFUSALS[status.HTTP_403_FORBIDDEN],
    status.HTTP_409_CONFLICT: {
        "model": ErrorResponse,
        "description": (
            "`the_tap_window_is_open` — the first 30 minutes are not over: tap "
            "*I'm here* at the club instead.\n\n"
            "`the_late_claim_has_closed` — the day after the tap window "
            "(`attendance[].claim_by`) is over: *Didn't come* is final.\n\n"
            "`nobody_said_they_were_not_here` — nobody tapped you.\n\n"
            "`already_arrived` — your arrival is already noted.\n\n"
            "`nothing_to_confirm` — they haven't said *I was there*.\n\n"
            "`you_are_not_here_yourself` — you Didn't come yourself, so you "
            "can't vouch for anybody.\n\n"
            "`attendance_is_for_booked_games` — a game with no hour."
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
        "entry, one awaiting an answer and one that is over are one thing at "
        "three moments of its life.\n\n"
        "**The standing is derived, never stored.** It is folded from the record "
        "and the clock at the moment you asked, so a full game whose entry "
        "window ran out with nobody recording it reads `PLAYED_NO_SCORE` whether "
        "or not anything has swept it — nothing sweeps it, because there is "
        "nothing for a sweep to correct.\n\n"
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
        "**The game screen's forecast, split, stakes, Levels and — on For fun "
        "— Social vibe, computed when you ask.** Nothing here is stored on the "
        "game, and nothing on "
        "`GET /games` changes: a seat there still carries a name and nothing "
        "else.\n\n"
        "**Read in your direction.** `split.gap` is your side's strength minus "
        "theirs, and `at_stake` is what a counted result would do to *your* "
        "Level — the rating engine's own rule read forward, side against side, "
        "so it is the pair the result will deliver.\n\n"
        "**Each block is omitted on its own ground.** `forecast` and "
        "`split` are omitted together when the pairing cannot be computed — "
        "somebody on the court holds no rating in the sport, or a seat could "
        "not be priced — and there is deliberately no reason beside the "
        "absence. `at_stake` is omitted on a friendly, where a counted result "
        "is meaningless rather than unavailable, and where the rule has nothing "
        "to move or nothing to price against — you hold no rating in the sport, "
        "or nobody across the net does. `seats` names the Level of everybody "
        "the platform holds one for.\n\n"
        "**A For-fun game carries its Social vibe** (`vibe`, #835): the "
        "court's number — the one its card and its details showed — and a row "
        "for each of your tags, naming who on the court carries it, worked "
        "out from everybody's tags now. Omitted on a competitive game, while "
        "a seat is open, and where nobody holds a tag that counts. The "
        "forecast is still sent on a For-fun game, for the apps already on "
        "phones; draw the vibe in its place.\n\n"
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
    "/{game_id}/attendance/not-here-yet",
    response_model=GameSchema,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"description": "The game as it stands with them awaited."},
        **_AT_THE_COURT_REFUSALS,
    },
    summary="Say somebody isn't here yet",
    description=(
        "***Oscar isn't here yet*** — on a **booked** game, from its start until "
        "30 minutes after it, about somebody else on the court, partner "
        "included (#657). **Made at the club**: `location` is the fix the phone "
        "read at the tap, measured against the club's map point and dropped — "
        "only *at the club* is kept. It costs you nothing, and saying it of "
        "somebody already awaited answers the same and writes nothing.\n\n"
        "Their **arrival** — their own *I'm here*, or anybody's *they're "
        "here* — decides what it was: **on time** within 10 minutes of the "
        "start (nothing is recorded), **Came late** up to 30, and **Didn't "
        "come** with no arrival by then (`attendance[].arrive_by`): the game "
        "takes no score and never counts."
    ),
)
async def note_absent(
    game_id: UUID,
    payload: NotHereYetRequest,
    user: CurrentUserDep,
    use_case: NoteAbsentDep,
) -> GameSchema:
    return GameSchema.of(
        await use_case.execute(
            NoteAbsentCommand(
                game_id=game_id,
                player_id=user.id,
                absent_id=payload.player_id,
                fix=payload.location.as_fix(),
            )
        ),
        reader_id=user.id,
    )


@router.post(
    "/{game_id}/attendance/arrival",
    response_model=GameSchema,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "The game as it stands with their arrival noted."
        },
        **_AT_THE_COURT_REFUSALS,
    },
    summary="Say you're here, or they're here",
    description=(
        "***I'm here*** with your own id, ***they're here*** with a "
        "courtmate's — about somebody tapped *isn't here yet*, from the club, "
        "before 30 minutes after the start (#657). **The first arrival is the "
        "one that counts**, and its moment decides: on time within 10 minutes "
        "of the start, Came late after. *They're here* is checked at the club "
        "too."
    ),
)
async def note_arrival(
    game_id: UUID,
    payload: ArrivalRequest,
    user: CurrentUserDep,
    use_case: NoteArrivalDep,
) -> GameSchema:
    return GameSchema.of(
        await use_case.execute(
            NoteArrivalCommand(
                game_id=game_id,
                player_id=user.id,
                arrived_id=payload.player_id,
                fix=payload.location.as_fix(),
            )
        ),
        reader_id=user.id,
    )


@router.post(
    "/{game_id}/attendance/claim",
    response_model=GameSchema,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"description": "The game as it stands with your claim."},
        **_LATE_CLAIM_REFUSALS,
    },
    summary="Say you were there",
    description=(
        "***I was there*** — you Didn't come, and your phone died at the court "
        "(#657). Within a day of the tap window closing "
        "(`attendance[].claim_by`), from wherever you are: **no location is "
        "asked**, because what proves it is somebody else on the court "
        "confirming it. Until they do, you still Didn't come. A second claim "
        "answers the same and writes nothing."
    ),
)
async def claim_presence(
    game_id: UUID,
    user: CurrentUserDep,
    use_case: ClaimPresenceDep,
) -> GameSchema:
    return GameSchema.of(
        await use_case.execute(
            ClaimPresenceCommand(game_id=game_id, player_id=user.id)
        ),
        reader_id=user.id,
    )


@router.post(
    "/{game_id}/attendance/confirmation",
    response_model=GameSchema,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "The game as it stands with your confirmation."
        },
        **_LATE_CLAIM_REFUSALS,
    },
    summary="Say they were here",
    description=(
        "***Yes, they were here*** — about somebody else's *I was there*, inside "
        "the same day (#657). **It turns Didn't come into Came late**, because "
        "the tap still proves they weren't there when it was made, and the game "
        "carries on as usual — a score, and the Level with it. In singles, the "
        "one who can confirm is the opponent who tapped. A second confirmation "
        "answers the same and writes nothing."
    ),
)
async def confirm_presence(
    game_id: UUID,
    payload: PresenceConfirmationRequest,
    user: CurrentUserDep,
    use_case: ConfirmPresenceDep,
) -> GameSchema:
    return GameSchema.of(
        await use_case.execute(
            ConfirmPresenceCommand(
                game_id=game_id, player_id=user.id, claimant_id=payload.player_id
            )
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

    A For-fun game's vibe is read beside the pairing and drawn on its own
    ground (#835), so it crosses whether or not the Levels could be read.
    """

    pairing = one.pairing
    fields: dict[str, Any] = {"read_at": one.read_at, "seats": []}
    if one.vibe is not None:
        fields["vibe"] = {
            "pct": one.vibe.pct,
            "rows": [
                {"tag": row.tag, "carried_by": list(row.carried_by)}
                for row in one.vibe.rows
            ],
        }
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
