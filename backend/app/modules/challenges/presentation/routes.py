"""The four challenge routes: send one, read yours, answer a seat either way.

**All four are on the player surface.** The one that looks like a console's — a
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
    SeatChoice,
    SendChallengeCommand,
)
from app.modules.challenges.application.read_challenges import (
    ReadChallengesCommand,
    StandingChallenge,
)
from app.modules.challenges.presentation.dependencies import (
    AcceptSeatDep,
    DeclineSeatDep,
    ReadChallengesDep,
    SendChallengeDep,
)
from app.modules.challenges.presentation.schemas import (
    ChallengeListResponse,
    ChallengeSchema,
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
        "**Each invitee gets 24 hours from when *their* seat was invited**, so a "
        "seat filled later is not already half expired.\n\n"
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
        "**Ended challenges are here too**, carrying `DECLINED` or `LAPSED`. A "
        "list that quietly dropped this morning's is a list that lies.\n\n"
        "**This is also the remedy for `open_challenge_stands`.** A refused send "
        "names nobody; read this to find out which of your own open games is in "
        "the way."
    ),
)
async def read_challenges(
    user: CurrentUserDep,
    use_case: ReadChallengesDep,
) -> ChallengeListResponse:
    found = await use_case.execute(ReadChallengesCommand(reader_id=user.id))
    return ChallengeListResponse(challenges=[_challenge(one) for one in found])


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
            "already drawn."
        ),
    },
}


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


def _challenge(one: StandingChallenge) -> ChallengeSchema:
    """One challenge as its court is allowed to see it.

    The occupants are bare ids: a card, a Level and an area belong to a search's
    answer, where a gate decided they may be shown. A challenge is a fact about
    an arrangement, and a screen that quietly re-published somebody's profile off
    the back of it would be a directory with extra steps.
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
        seats=[
            SeatSchema(
                side=seat.side,
                player_id=seat.player_id,
                answer=seat.answer,
                answer_by=seat.answer_by,
            )
            for seat in challenge.seats
        ],
    )
