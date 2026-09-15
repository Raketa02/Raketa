"""The challenge routes: send one, read yours, read one richly, answer a seat
either way, grow a half-built one, end one — and leave the game one became.

**All of them are on the player surface.** The one that looks like a console's — a
read of your own pending challenges — is not: an invitee has to be able to find
that they were asked, and *Now* is where a sent challenge lands. The dev console
consumes the same routes by signing in as a seeded player, which is why there is
no impersonation endpoint and no ``Act-As`` header anywhere in this repository.

**The send is one act, and it refuses whole.** Five facts are re-verified in its
own transaction — the four fail-closed gates a stored search's read-back already
re-evaluates, plus the open-challenge pair rule the gate roster deliberately
leaves soft. A refused send writes nothing.

**No refusal names anybody.** The organiser finds out *who* by re-reading the two
sources they already own: the origin search, whose read-back marks the rows it
withholds, and their own challenges, which were always theirs to read.

**Answering is not gated.** The gates run when a challenge is *minted*, because
that is the act that puts two people in front of each other; refusing an answer on
one would tell the answerer that something changed about somebody else on the
court, which is the one thing a safety gate may never say.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, status

from app.core.exception_handlers import ErrorResponse
from app.modules.challenges.application.commands import (
    AnswerSeatCommand,
    FillSeatsCommand,
    LeaveGameCommand,
    SeatChoice,
    SendChallengeCommand,
    WithdrawChallengeCommand,
)
from app.modules.challenges.application.read_challenge import (
    DetailedChallenge,
    ReadChallengeCommand,
)
from app.modules.challenges.application.read_challenges import (
    ReadChallengesCommand,
    StandingChallenge,
)
from app.modules.challenges.domain.answer_window import ANSWER_WINDOW_HOURS
from app.modules.challenges.domain.ports import CourtCard
from app.modules.challenges.domain.seats import Seat
from app.modules.challenges.presentation.dependencies import (
    AcceptSeatDep,
    DeclineSeatDep,
    FillSeatsDep,
    LeaveGameDep,
    ReadChallengeDep,
    ReadChallengesDep,
    SendChallengeDep,
    WithdrawChallengeDep,
)
from app.modules.challenges.presentation.schemas import (
    ChallengeDetailResponse,
    ChallengeListResponse,
    ChallengeSchema,
    FillSeatsRequest,
    SeatSchema,
    SendChallengeRequest,
    SentChallengeResponse,
)
from app.modules.users.presentation.dependencies import CurrentUserDep

router = APIRouter(prefix="/challenges", tags=["challenges"])

_REFUSALS: dict[int | str, dict[str, Any]] = {
    status.HTTP_403_FORBIDDEN: {
        "model": ErrorResponse,
        "description": (
            "`account_held` — **your** account is under a live hold. The same "
            "code a search returns, and refused at the entry point: a hold that "
            "stops you searching but lets you send invitations is the same hole "
            "with the blast radius pointed at other people."
        ),
    },
    status.HTTP_400_BAD_REQUEST: {
        "model": ErrorResponse,
        "description": (
            "`challenge_with_no_invitee`, `organiser_holds_a_seat`, "
            "`one_person_to_a_seat`, `cannot_challenge_yourself` — who is on "
            "the court, and every one of them a caller's bug. Checked "
            "**first, before anything is read**, because they are true "
            "regardless of anybody else's state: telling an organiser their "
            "line-up went stale when they invited nobody sends them refreshing "
            "a screen that was never wrong.\n\n"
            "`court_is_not_the_sports` — the seats are not "
            "`2 x seats_per_side`, evenly split, in the court's own order. The "
            "one refusal in that family that cannot come first: the shape is "
            "the sport's, and the sport is the search's to say."
        ),
    },
    status.HTTP_409_CONFLICT: {
        "model": ErrorResponse,
        "description": (
            "`court_origin_not_found` — no search of yours showed all of those "
            "players. One code for four cases, on purpose.\n\n"
            "`line_up_no_longer_sendable` — somebody on this court can no longer "
            "be invited to it. **Which one is deliberately not said, and neither "
            "is why.** Re-read the origin search: its read-back re-evaluates the "
            "same gates and marks the seats. **Do not re-run the search** — that "
            "mints a new `search_id` the whole line-up must adopt, and its "
            "untouched seats are only *probably* in the new answer.\n\n"
            "`open_challenge_stands` — two people on this court already have a "
            "game between them, **in any sport**. Read your own challenges to "
            "find out who; an open game of yours was always yours to read."
        ),
    },
    status.HTTP_503_SERVICE_UNAVAILABLE: {
        "model": ErrorResponse,
        "description": (
            "`challenge_gates_unavailable` — a safety gate could not be read, so "
            "nothing was minted. Transient and about the platform: retry the same "
            "request."
        ),
    },
}


@router.post(
    "",
    response_model=SentChallengeResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {
            "description": (
                "The challenge stands, and everybody on the court has been asked."
            ),
        },
        **_REFUSALS,
    },
    summary="Send the challenge",
    description=(
        "**One act, everybody at once.** A doubles send is one challenge "
        "containing four people, answered by each of them separately — never "
        "three separate invitations.\n\n"
        "**Your own seat is accepted from birth.** You are the one proposing, so "
        "nothing asks whether you want to play the game you just built.\n\n"
        # The one duration this surface names, and it is **read, never typed**:
        # a description spelling its own copy would be a promise going quietly
        # wrong the day ``answer_window.py`` moved — which it has
        # (``docs/adr/0151``). No *player* sentence names one at all; they render
        # a seat's own ``answer_by``, which is why the window doubled without a
        # string changing.
        f"**Each invitee gets {ANSWER_WINDOW_HOURS} hours from when *their* "
        "seat was invited**, so a seat filled later is not already half "
        "expired.\n\n"
        "**The arrangement you built is what is recorded**, and it is what they "
        "answer — never a better one worked out afterwards.\n\n"
        "**Everything is re-checked here**, in one transaction, because your "
        "line-up may be an hour old and nothing refetches it in the background. "
        "The send either happens whole or writes nothing at all: there is no "
        "partial send that quietly drops one person.\n\n"
        "**The sport, the kind of evening and the week come from the search**, "
        "not from this request. There is no window picker anywhere — you change "
        "your window by changing your grid."
    ),
)
async def send_challenge(
    payload: SendChallengeRequest,
    user: CurrentUserDep,
    use_case: SendChallengeDep,
) -> SentChallengeResponse:
    challenge_id = await use_case.execute(
        SendChallengeCommand(
            organiser_id=user.id,
            search_id=payload.search_id,
            court=tuple(
                SeatChoice(side=seat.side, player_id=seat.player_id)
                for seat in payload.court
            ),
        )
    )
    return SentChallengeResponse(challenge_id=challenge_id)


@router.get(
    "",
    response_model=ChallengeListResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": (
                "Every challenge you hold a seat in, newest first, each with what "
                "it is right now."
            ),
        },
    },
    summary="Your challenges",
    description=(
        "**Sent and received in one list.** *Challenge sent* and *Challenge for "
        "you* are one standing read from two sides; tell them apart by whether "
        "`organiser_id` is yours.\n\n"
        "**The standing is derived, never stored.** It is folded from the seats "
        "and the clock at the moment you asked, so a seat whose day ran out reads "
        "as lapsed whether or not anything has swept it yet.\n\n"
        "**Ended challenges are here too**, carrying `DECLINED`, `LAPSED` or "
        "`WITHDRAWN`. A list that quietly dropped this morning's is a list that "
        "lies.\n\n"
        "**This is also the remedy for `open_challenge_stands`.** A refused send "
        "names nobody; read this to find out which of your own open games is in "
        "the way."
    ),
)
async def read_challenges(
    user: CurrentUserDep,
    use_case: ReadChallengesDep,
) -> ChallengeListResponse:
    read_at, found = await use_case.execute(
        ReadChallengesCommand(reader_id=user.id)
    )
    return ChallengeListResponse(
        read_at=read_at, challenges=[_challenge(one) for one in found]
    )


_ANSWER_REFUSALS: dict[int | str, dict[str, Any]] = {
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponse,
        "description": (
            "`challenge_not_found` — no challenge of **yours** has that id. One "
            "code for two cases — it does not exist, or you are not on its court "
            "— because separating them would answer *is this id real* about a "
            "stranger's evening."
        ),
    },
    status.HTTP_409_CONFLICT: {
        "model": ErrorResponse,
        "description": (
            "`seat_already_answered` — you have answered this one. **Not "
            "idempotent, deliberately**: *yes* after *no* is a different answer "
            "and not a repeat of one.\n\n"
            "`answer_window_has_passed` — your day ran out. The seat already "
            "reads as lapsed and may have been offered to somebody else, so an "
            "answer that resurrected it would contradict a card the platform has "
            "already drawn.\n\n"
            "`game_moment_has_passed` — **on a court somebody left**, the moment "
            "the plan agreed has passed, so a yes now would seat you into a game "
            "whose moment is gone. `game_is_history` — that game has happened, "
            "or never will. Neither is reachable on a court that was never a "
            "game.\n\n"
            "`challenge_is_over` — the organiser removed this challenge while "
            "your day was still running. Your seat has nothing of its own to "
            "refuse, and the court is over; the answer is refused rather than "
            "recorded on a challenge nobody is arranging any more."
        ),
    },
}


@router.get(
    "/{challenge_id}",
    response_model=ChallengeDetailResponse,
    response_model_exclude_unset=True,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": (
                "The arrangement, the people on it, and what you make of each "
                "of them."
            ),
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": (
                "`challenge_not_found` — no challenge of **yours** has that id. "
                "One code for two cases — it does not exist, or you are not on "
                "its court — because separating them would answer *is this id "
                "real* about a stranger's evening."
            ),
        },
    },
    summary="One challenge",
    description=(
        "**The screen you answer on.** The list tells you what you have been "
        "asked; this tells you who is asking and what this platform makes of "
        "playing them.\n\n"
        "**The pairing is computed when you open this, in your own "
        "direction.** Nothing is copied at send and nothing is replayed from "
        "the organiser's search — which is why a challenge born of a mutual "
        "yes draws the same screen as one built from a shortlist, and why the "
        "Fit here is genuinely yours.\n\n"
        "**The card block is drawn while the arrangement is being decided and "
        "at no other time.** A challenge that ended draws its arrangement and "
        "the names alone, and so does the seat of somebody who declined or "
        "lapsed inside one that is still open: they have left, and that person "
        "is a stranger to you again.\n\n"
        "**Answering is never gated on any of it.** If the pairing cannot be "
        "computed — you hold no rating in this sport, or something the matcher "
        "needs could not be read — `pairing_absence` says which, the "
        "arrangement answers as always, and the buttons are drawn from the "
        "standing.\n\n"
        "**Nothing here is re-checked against who is reading.** The safety "
        "gates ran when this challenge was minted, in both directions, and "
        "they are not run again."
    ),
)
async def read_challenge(
    challenge_id: UUID,
    user: CurrentUserDep,
    use_case: ReadChallengeDep,
) -> ChallengeDetailResponse:
    return _detailed(
        await use_case.execute(
            ReadChallengeCommand(challenge_id=challenge_id, reader_id=user.id)
        ),
        reader_id=user.id,
    )


@router.post(
    "/{challenge_id}/accept",
    response_model=ChallengeSchema,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "Your seat is accepted, and the challenge as it now stands."
        },
        **_ANSWER_REFUSALS,
    },
    summary="Accept your seat",
    description=(
        "**Your yes matters on its own**, and is not conditional on the other "
        "seats: the conversation opens on the *first* acceptance and grows with "
        "each one, so there is no waiting room and no single moment where the "
        "game becomes real.\n\n"
        "**The seat is not in the path** because you hold at most one in any "
        "challenge — and nobody may answer for anybody else.\n\n"
        "The challenge reads `ON` once **every** seat is accepted, with no "
        "special case for the organiser and none for singles."
    ),
)
async def accept_seat(
    challenge_id: UUID,
    user: CurrentUserDep,
    use_case: AcceptSeatDep,
) -> ChallengeSchema:
    return _challenge(
        await use_case.execute(
            AnswerSeatCommand(challenge_id=challenge_id, player_id=user.id)
        )
    )


@router.post(
    "/{challenge_id}/decline",
    response_model=ChallengeSchema,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": (
                "Your seat is open again, and the challenge as it now stands."
            )
        },
        **_ANSWER_REFUSALS,
    },
    summary="Decline your seat",
    description=(
        "**Your no is about you.** It reopens exactly your seat and disturbs "
        "nothing else: the people who already agreed did nothing wrong and are "
        "still in the game, and the organiser may offer your seat to somebody "
        "else.\n\n"
        "**Nobody is told you declined**, and no response anywhere names you as "
        "having done so.\n\n"
        "**Saying nothing is not this.** Silence past your day is a *lapse*, "
        "which is a different fact and is counted apart — the platform never "
        "files it as a judgement you made."
    ),
)
async def decline_seat(
    challenge_id: UUID,
    user: CurrentUserDep,
    use_case: DeclineSeatDep,
) -> ChallengeSchema:
    return _challenge(
        await use_case.execute(
            AnswerSeatCommand(challenge_id=challenge_id, player_id=user.id)
        )
    )


@router.post(
    "/{challenge_id}/seats",
    response_model=ChallengeSchema,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": (
                "The seats are filled and the court is returned as it now "
                "stands. Everybody newly seated has their **own** day from this "
                "moment."
            )
        },
        status.HTTP_404_NOT_FOUND: _ANSWER_REFUSALS[status.HTTP_404_NOT_FOUND],
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorResponse,
            "description": (
                "`account_held` — **your** account is under a live hold, and a "
                "hold that let you invite people would be the same hole with the "
                "blast radius pointed at them.\n\n"
                "`fill_is_the_live_members` — you hold a seat on this court and "
                "you have left it. **Not a 404**: your own seat is still drawn "
                "on the challenge, so pretending it is not there would be the "
                "wrong lie."
            ),
        },
        status.HTTP_400_BAD_REQUEST: _REFUSALS[status.HTTP_400_BAD_REQUEST],
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": (
                "`court_origin_not_found` — no search of yours showed all of the "
                "people you are newly asking. One code for four cases, on "
                "purpose. **The people already on the court are not looked up in "
                "it**, so a court that keeps them is not refused for them.\n\n"
                "`line_up_no_longer_sendable` — somebody on this court can no "
                "longer be invited to it. **Which one is deliberately not said, "
                "and neither is why.** Re-read the challenge and the origin "
                "search.\n\n"
                "`open_challenge_stands` — two people on this court already have "
                "a game between them **in any sport**, and it is not this one: "
                "this court's own pairs are excepted, and no other challenge "
                "is.\n\n"
                "`nobody_new_to_invite` — every seat on the court you posted is "
                "already taken by somebody in the game. **The court is not "
                "grown, and nothing is written.**\n\n"
                "`nobody_is_asked_twice` — somebody on that court has already "
                "answered this challenge. Unreachable through the builder, which "
                "does not offer them; this is the aggregate's backstop.\n\n"
                "`accepted_player_may_not_be_removed` — a court that dropped "
                "somebody who is already in.\n\n"
                "`challenge_is_over` — this challenge has ended.\n\n"
                "`game_moment_has_passed`, `game_is_history` — **on a court "
                "somebody left**: the game's agreed moment has passed, or the "
                "game has happened or never will, so nobody may be seated into "
                "it. Neither is reachable on a court that was never a game."
            ),
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: _REFUSALS[
            status.HTTP_503_SERVICE_UNAVAILABLE
        ],
    },
    summary="Fill the open seats",
    description=(
        "**Grows a court that is already standing**, from a line-up you just "
        "built. The people who accepted keep their places and their answers; the "
        "open seats are offered to the people you name.\n\n"
        "**Any live member may do this** — growing a court and ending one are "
        "different acts: removing a challenge is the organiser's while nobody "
        "has joined and nobody's once somebody has, and calling off the game a "
        "court became is any player's on it. A challenge born of "
        "two mutual yeses has an organiser who is only whoever said yes second, "
        "and leaving the other one unable to finish the four would make an "
        "arbitrary tiebreak decide whose game it is. Somebody who declined or "
        "let their day run out is **not** a live member.\n\n"
        "**Post the whole court, not the new seats.** An acceptance is to the "
        "game and not to the side, so you may move somebody across the net — and "
        "you may never take them out.\n\n"
        f"**Each newly seated player gets their own {ANSWER_WINDOW_HOURS} "
        "hours**, dated from this moment. A seat filled later is not already "
        "half expired, and nobody's existing deadline moves.\n\n"
        "**The window is not re-stamped.** The week this challenge was proposed "
        "for was fixed when it was sent, and a challenge born of a mutual yes "
        "has none at all — the plan, not the window, is what says when anybody "
        "actually plays.\n\n"
        "**Everything is re-checked here**, in one transaction, exactly as a "
        "send is: the four fail-closed gates over the whole court, and the "
        "open-challenge rule with **this** challenge excepted and no other. The "
        "fill either happens whole or writes nothing.\n\n"
        "**Somebody who let your invitation run out is out of this court's own "
        "pool, and out of nothing else.** Nobody is asked twice on one "
        "challenge, so they are not a candidate for this fill for as long as "
        "this court stands — and asking them again is a **new** challenge rather "
        "than a seat on this one. Every **other** search of yours reaches them "
        "immediately, in any sport: their seat reopened and the open-challenge "
        "rule released them with it."
    ),
)
async def fill_seats(
    challenge_id: UUID,
    payload: FillSeatsRequest,
    user: CurrentUserDep,
    use_case: FillSeatsDep,
) -> ChallengeSchema:
    return _challenge(
        await use_case.execute(
            FillSeatsCommand(
                challenge_id=challenge_id,
                player_id=user.id,
                search_id=payload.search_id,
                court=tuple(
                    SeatChoice(side=seat.side, player_id=seat.player_id)
                    for seat in payload.court
                ),
            )
        )
    )


@router.post(
    "/{challenge_id}/withdrawal",
    response_model=ChallengeSchema,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": (
                "The challenge is over, and it is returned as it now stands — "
                "`WITHDRAWN` on a court that was never a game, `CALLED_OFF` on "
                "one that has been, `ended_by` naming you either way — with "
                "every seat exactly as it was: a seat still awaiting an answer "
                "keeps its question and its deadline, and the standing is read "
                "before either."
            )
        },
        status.HTTP_404_NOT_FOUND: _ANSWER_REFUSALS[status.HTTP_404_NOT_FOUND],
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorResponse,
            "description": (
                "`withdraw_is_the_organisers` — you hold a seat on this court "
                "and the act is not yours. On a court that was never a game, "
                "removing the challenge is the organiser's alone; on one that "
                "has been a game, calling it off is any player's **on the "
                "court** — an accepted seat — so somebody who left, the "
                "organiser who left, and a newcomer still deciding on a fill "
                "are all told this. **Not a 404**: you can already see this "
                "challenge, so pretending it is not there while your own seat "
                "is drawn on it would be the wrong lie."
            ),
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": (
                "`somebody_has_joined` — somebody besides you holds an accepted "
                "seat on a court that was never a game, so it is no longer "
                "yours to remove for the others. Leave it instead "
                "(`POST /challenges/{id}/departure`); it ends by itself when "
                "one is left with nobody deciding.\n\n"
                "`not_a_half_built_line_up` — the court has been a game and "
                "has no seat to call it off for: it is whole (`ON`), or a "
                "newcomer is still deciding on its open seat "
                "(`AWAITING_ANSWERS` after a fill). One code for the two, "
                "because they are one sentence and the standing already says "
                "which.\n\n"
                "`challenge_is_over` — this challenge has ended, this act "
                "included: a second press meets it."
            ),
        },
    },
    summary="Remove the challenge, or call the game off",
    description=(
        "**Two acts on one route, and which one this is turns on whether the "
        "court has been a game.**\n\n"
        "**Remove the challenge** — on a court that was never a game. The "
        "organiser's, and admitted exactly while **nobody besides the organiser "
        "holds an accepted seat**: before anybody has answered, and again once "
        "everybody who joined has left — whatever seats are still deciding. "
        "The moment somebody has joined it is refused: a court somebody has "
        "joined is nobody's to end for the others, so from then on the "
        "organiser leaves it like anybody else, and it is over by itself when "
        "at most one player is on it and nobody is still deciding. The "
        "invitees' challenges read `WITHDRAWN` and offer no answer — a yes or "
        "a no on a removed challenge is refused with `challenge_is_over` — and "
        "an invitation whose day was still running is neither answered nor "
        "unanswered: it leaves the record that prices silence, and the lapse "
        "loop writes nothing for it.\n\n"
        "**Call it off** — on a court that has been a game and lost somebody. "
        "The court is half built again, and this is how the game is called "
        "off: the challenge records its own ending, `CALLED_OFF` with "
        "`ended_by` you — **never `WITHDRAWN`**, which is *Remove the "
        "challenge*'s alone — and the game it became reaches its fourth end, "
        "`CALLED_OFF` with `called_off_by` you, in the same act: its plan is "
        "history, its pairing is history, and it is neither an evening nor a "
        "game that never happened, so nothing anybody is measured on moves. "
        "**Any player on the court**, the organiser or not, and only while a "
        "seat is open with nobody deciding on it: a full court that will not "
        "play lets its window lapse into `NEVER_PLAYED`, as it always has. A "
        "court whose game's window has already closed is called off all the "
        "same, with you on its record, and the game stays the ghost it "
        "already is. A court whose game a departure already called off is "
        "over, and this meets `challenge_is_over`.\n\n"
        "**Whole-challenge, and it never removes one person.** A withdraw ends "
        "the arrangement for everybody on it, and taking one person out of a "
        "court that still stands is refused here as it is everywhere else.\n\n"
        "**Irreversible.** There is no route back. Asking the same people again "
        "is a **new** challenge, with fresh deadlines and its own record of who "
        "has answered — which is what it actually is. That a removal can be "
        "followed by a resend to the same person, on a fresh clock, is a named "
        "and accepted risk with its falsifier written down.\n\n"
        "**What this releases is the people on the court.** A send holds its "
        "pairs for as long as an answer is owed, and a reopened court holds "
        "its pair until it is re-seated or called off; this is that exit. "
        "Somebody who let their day run out needed none: their seat reopened "
        "and the open-challenge rule released them with it.\n\n"
        "**A noun and not a verb**, because what this creates is the ending — "
        "the withdrawal, or the court's call-off — which are the two things in "
        "this context that a fold of the seats could never produce. The "
        "conversation is destroyed in the act where one exists: there is none "
        "before anybody has answered, there may be one the organiser is alone "
        "in again, and a court that has been a game has one."
    ),
)
async def withdraw_challenge(
    challenge_id: UUID,
    user: CurrentUserDep,
    use_case: WithdrawChallengeDep,
) -> ChallengeSchema:
    return _challenge(
        await use_case.execute(
            WithdrawChallengeCommand(challenge_id=challenge_id, player_id=user.id)
        )
    )


@router.post(
    "/{challenge_id}/departure",
    response_model=ChallengeSchema,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": (
                "Your seat is open again, and the challenge as it now stands. "
                "`LINE_UP_INCOMPLETE` where the others are in — on a game, that "
                "game survives with your seat empty; `AWAITING_ANSWERS` where "
                "somebody is still deciding; `DECLINED` where you were the "
                "last but one on a court that was never a game and nobody is "
                "deciding — **a court is over when at most one player is on it "
                "and no seat is awaiting an answer**, and a departure is a no; "
                "and `CALLED_OFF` where you were the last but one on a court "
                "that has been a game: the court ends with its game, `ended_by` "
                "you, and the game is called off in this same request — "
                "`GET /games` reads it `CALLED_OFF` with `called_off_by` you, "
                "and the room is gone."
            )
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": (
                "`challenge_not_found` — no challenge of **yours** has that id, "
                "or you hold no **accepted** seat on it. One code for three "
                "cases: it does not exist, you are not on its court, or your seat "
                "is awaiting, declined, lapsed or already left — because a "
                "departure is the one act whose refusal must not confirm that "
                "you *were* on this court a moment ago."
            ),
        },
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorResponse,
            "description": (
                "`account_held` — **your** account is under a live hold. A "
                "departure writes a line into a room other people are in, which "
                "is reach."
            ),
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": (
                "`challenge_is_over` — this challenge has ended.\n\n"
                "`game_is_history` — the game has happened, was called off, or "
                "its entry window closed on silence. The line-up is the record "
                "of an evening, and nothing on it moves.\n\n"
                "`game_moment_has_passed` — the moment the plan agreed has "
                "passed. Leaving would mean nothing now, and a no-show cannot "
                "vacate a seat to block the result. **Only where there is a "
                "game**: a half-built court may carry a plan naming a moment, "
                "and has no moment to guard.\n\n"
                "There is no `not_a_game_yet` any more: a yes can be taken back "
                "before the court is whole."
            ),
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: _REFUSALS[
            status.HTTP_503_SERVICE_UNAVAILABLE
        ],
    },
    summary="Leave the game",
    description=(
        "**You are out of a court you had agreed to** — a game, or a court "
        "that is not whole yet. Your seat reopens on the challenge; where the "
        "court had become a game, that game survives with your seat drawn "
        "empty, and the people still on it keep what they agreed — the plan, "
        "the room, the record. Anyone still on the court may fill your seat "
        "the way a half-built court is filled, and the newcomer's yes re-seats "
        "the **same** game.\n\n"
        "**Any player on the court, the organiser included**, while the court "
        "stands — and, on a game, while it is awaiting its entry and its agreed "
        "moment is ahead or no moment is agreed yet. Once the moment has "
        "passed, leaving means nothing and is refused; a court that is not a "
        "game has no moment to guard.\n\n"
        "**A court is over when at most one player is on it and no seat is "
        "awaiting an answer**, and the organiser is a player in that rule. "
        "Before a game the challenge ends by itself — as `DECLINED`, because a "
        "departure is a no — and its room with it. On a game, the departure "
        "that leaves one player on it **ends the court with its game** in "
        "this request: the challenge reads `CALLED_OFF` naming you, `GET "
        "/games` reads `CALLED_OFF` naming you, and the room is gone. Singles "
        "included: an opponent who leaves calls the game off — for the person "
        "they leave, too.\n\n"
        "**You are out of this court's own pool for as long as it stands.** "
        "Nobody is asked twice on one challenge; being asked again is a **new** "
        "challenge. Every other search reaches you at once — the pair rule "
        "released you the moment you left.\n\n"
        "**The others are told**: the room draws *{name} left — that seat is "
        "open again*, and your own list and inbox no longer hold the game or "
        "the room.\n\n"
        "**Two people may leave**, and two seats may be open. Nothing here "
        "prices a departure yet — it is recorded, with its moment, and that is "
        "all.\n\n"
        "**A noun and not a verb**, like the withdrawal: what this creates is "
        "the departure."
    ),
)
async def leave_game(
    challenge_id: UUID,
    user: CurrentUserDep,
    use_case: LeaveGameDep,
) -> ChallengeSchema:
    return _challenge(
        await use_case.execute(
            LeaveGameCommand(challenge_id=challenge_id, player_id=user.id)
        )
    )


def _challenge(one: StandingChallenge) -> ChallengeSchema:
    """One challenge as its court is allowed to see it.

    **The occupants carry a name and nothing else** (``docs/adr/0143`` §7). A
    Level, a band, an area and a photograph are what a *card* carries, and a card
    is as-of-now: it belongs on the detail read, where the arrangement is still
    being decided and the person reading is doing what a searcher does. A list
    that drew one would be a directory with extra steps, priced over somebody's
    whole history of being asked.

    A name passes ``docs/adr/0141`` §1's test instead: it is what these people
    were already calling each other, and nothing a gate decided somebody may see.
    """

    challenge = one.challenge
    return ChallengeSchema(
        challenge_id=challenge.id,
        sport=challenge.sport,
        mode=challenge.mode,
        window=challenge.window,
        organiser_id=challenge.organiser_id,
        standing=one.standing,
        opened_at=challenge.opened_at,
        ended_at=one.ended_at,
        ended_by=one.ended_by,
        game_id=one.game_id,
        seats=[
            SeatSchema(
                side=seat.side,
                player_id=seat.player_id,
                answer=seat.answer,
                answer_by=seat.answer_by,
                name=(
                    None
                    if seat.player_id is None
                    else one.names.get(seat.player_id)
                ),
            )
            for seat in challenge.seats
        ],
    )


def _detailed(one: DetailedChallenge, *, reader_id: UUID) -> ChallengeDetailResponse:
    """One challenge as the person answering it is allowed to see it.

    Built through ``model_validate`` over a dict rather than by keyword,
    because this route is declared ``response_model_exclude_unset=True`` and the
    two spellings of absence have to survive it: a key that is **not here** is
    *this does not apply* and generates as ``field?: T``, while a key present as
    ``None`` is *this applies and the answer is a measured nothing*. The seat's
    four list-read fields are therefore always set, ``null`` included, and the
    card block's are set only when they apply.
    """

    challenge = one.challenge
    fields: dict[str, Any] = {
        "read_at": one.read_at,
        "challenge_id": challenge.id,
        "sport": challenge.sport,
        "mode": challenge.mode,
        "window": challenge.window,
        "organiser_id": challenge.organiser_id,
        "standing": one.standing,
        "opened_at": challenge.opened_at,
        "seats": [
            _detailed_seat(one, seat, reader_id=reader_id)
            for seat in challenge.seats
        ],
    }
    if one.court is not None and one.court.absent is not None:
        fields["pairing_absence"] = one.court.absent
    return ChallengeDetailResponse.model_validate(fields)


def _detailed_seat(
    one: DetailedChallenge, seat: Seat, *, reader_id: UUID
) -> dict[str, Any]:
    """One seat, with its card where this read drew one.

    **Absent for four different reasons and the same way each time**: an empty
    seat, the reader's own, somebody who has left, and a read that produced no
    cards at all. Only the last of those has a code, on the response, because it
    is the only one the client cannot see for itself from the arrangement it is
    holding.
    """

    fields: dict[str, Any] = {
        "side": seat.side,
        "player_id": seat.player_id,
        "answer": seat.answer,
        "answer_by": seat.answer_by,
        "name": (
            None if seat.player_id is None else one.names.get(seat.player_id)
        ),
    }
    if seat.player_id is None or seat.player_id == reader_id:
        return fields
    card = one.card_for(seat.player_id)
    if card is not None:
        fields["card"] = _seat_card(card)
    return fields


def _seat_card(card: CourtCard) -> dict[str, Any]:
    """The two blocks, in this context's own narrower vocabulary.

    **The second mapper ``docs/adr/0143`` priced in its Consequences.** The
    person's three omissions and the pairing's two are each on their own terms:
    a photograph and its address travel together or not at all, a Player Score
    is absent where the platform has watched nothing, a distance is absent where
    the term stood down, and what is at stake is absent in for fun and where
    either player holds no rating.
    """

    person: dict[str, Any] = {
        "name": card.person.name,
        "area_code": card.person.area_code,
        "level": card.person.level,
        "band": card.person.band,
        "range": {"low": card.person.range_low, "high": card.person.range_high},
    }
    if card.person.photo_id is not None and card.person.photo_url is not None:
        person["photo_id"] = card.person.photo_id
        person["photo_url"] = card.person.photo_url
    if card.person.player_score is not None:
        person["player_score"] = card.person.player_score

    pairing: dict[str, Any] = {
        "fit": card.pairing.fit,
        # The same mappings the search record stores, validated here into this
        # context's own closed union. One serialiser, two consumers.
        "terms": [dict(term) for term in card.pairing.terms],
        "degraded_terms": [
            {"term": term, "reason": reason}
            for term, reason in card.pairing.degraded_terms
        ],
        "concerns": [{"term": term} for term in card.pairing.concerns],
    }
    if card.pairing.forecast is not None:
        pairing["forecast"] = {
            "pct": card.pairing.forecast.pct,
            "sigma_group": card.pairing.forecast.sigma_group,
            "provisional": card.pairing.forecast.provisional,
            "assumption": card.pairing.forecast.assumption,
        }
    if card.pairing.distance_km is not None:
        pairing["distance_km"] = card.pairing.distance_km
    if card.pairing.at_stake is not None:
        pairing["at_stake"] = {
            "win_delta": card.pairing.at_stake.win_delta,
            "loss_delta": card.pairing.at_stake.loss_delta,
        }
    return {"person": person, "pairing": pairing}
