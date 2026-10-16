"""A person's row: *Yes*, *No* and *Withdraw* on the cards they were dealt, as
them (``docs/adr/0194`` §2, §3; #590) — and *Leave the game*, *Take the seat*
and *No* on a rescue, *Post a game* at a court hour its sheet lists, and after
the game a score entered, agreed with or countered (#593) — and, at the court,
*isn't here yet*, *I'm here*, *they're here*, *I was there* and *yes, they were
here*, the first three **at the club or away** (#657). *Join* on a post they
were never dealt is the *Yes* here, as it is the phone's.

**Each route is the player's own route with the acting account in place of the
signed-in one** — ``POST /dev/as/{player_id}/proposals/{id}/yes`` beside the
player's ``POST /api/v1/proposals/{id}/yes`` — and runs the same use case,
built by the same dependency, with the same command. So a press does what that
person's own button would do, **refusals included**, and a refusal reaches the
page in the domain's own words, through the one error envelope.

**No logic of its own.** A route here is wiring: it builds the command and calls
the use case. If a player route ever does work outside its use case, the console
would skip it — that work moves into the use case, never into a copy here.
``tests/api/test_games_test_console.py`` holds each button to the player's route
over the same cases, refusals included.
"""

from __future__ import annotations

import app.api.dev.refusal  # noqa: F401 — refuses first; see refusal.py

from datetime import date
from enum import StrEnum
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Query, Response, status
from pydantic import BaseModel, Field

from app.api.dev.accounts import ActingDep
from app.core.exception_handlers import ErrorResponse
from app.engines.matchfit.core import SearchMode
from app.kernel import Sport, instant
from app.modules.games.application.commands import (
    AcceptResultCommand,
    ClaimPresenceCommand,
    ConfirmPresenceCommand,
    NoteAbsentCommand,
    NoteArrivalCommand,
    StateResultCommand,
)
from app.modules.games.domain.attendance import LocationFix
from app.modules.games.presentation.dependencies import (
    AcceptResultDep,
    ClaimPresenceDep,
    ConfirmPresenceDep,
    GameClubsDep,
    GameRepositoryDep,
    NoteAbsentDep,
    NoteArrivalDep,
    StateResultDep,
)
from app.modules.games.presentation.schemas import (
    GameSchema,
    PresenceConfirmationRequest,
    StateResultRequest,
)
from app.modules.proposals.application.commands import (
    AnswerProposalCommand,
    LeaveTheGameCommand,
    PostAGameCommand,
    PostingCommand,
    ReadPostingSlotCommand,
    RescueCommand,
)
from app.modules.proposals.domain.overlap import DayRange
from app.modules.proposals.domain.post import Who
from app.modules.proposals.presentation.dependencies import (
    JoinARescueDep,
    LeaveTheGameDep,
    PostAGameDep,
    ReadPostingSlotDep,
    SayNoDep,
    SayNoToARescueDep,
    SayYesDep,
    WithdrawYesDep,
)
from app.modules.proposals.presentation.schemas import (
    DepartureResponse,
    PostedResponse,
    PostingSlotResponse,
    PostRequest,
    YesAnswerResponse,
)

router = APIRouter(prefix="/as/{player_id}", tags=["dev"])

_REFUSED: dict[int | str, dict[str, Any]] = {
    status.HTTP_403_FORBIDDEN: {
        "model": ErrorResponse,
        "description": (
            "`not_a_seed_account` — the acting account is not one the seed "
            "created. Nothing was asked of the use case."
        ),
    },
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponse,
        "description": "As the player's own route answers it.",
    },
    status.HTTP_409_CONFLICT: {
        "model": ErrorResponse,
        "description": "As the player's own route answers it.",
    },
}


@router.post(
    "/proposals/{proposal_id}/yes",
    response_model=YesAnswerResponse,
    status_code=status.HTTP_200_OK,
    responses={
        **_REFUSED,
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ErrorResponse,
            "description": "As the player's own route answers it.",
        },
    },
    summary="Yes, as this person",
    description=(
        "`POST /api/v1/proposals/{id}/yes` as the acting account: the same use "
        "case, refusals included — and when it is the last, the fill, over the "
        "provider this process moves money through."
    ),
)
async def say_yes(
    proposal_id: UUID, acting: ActingDep, say: SayYesDep
) -> YesAnswerResponse:
    answer = await say.execute(
        AnswerProposalCommand(proposal_id=proposal_id, player_id=acting)
    )
    return YesAnswerResponse.from_answer(answer)


@router.post(
    "/proposals/{proposal_id}/no",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    responses=_REFUSED,
    summary="No, as this person",
    description=(
        "`POST /api/v1/proposals/{id}/no` as the acting account: silent, final, "
        "and never on their record."
    ),
)
async def say_no(proposal_id: UUID, acting: ActingDep, say: SayNoDep) -> Response:
    await say.execute(AnswerProposalCommand(proposal_id=proposal_id, player_id=acting))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/proposals/{proposal_id}/yes",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    responses=_REFUSED,
    summary="Withdraw, as this person",
    description=(
        "`DELETE /api/v1/proposals/{id}/yes` as the acting account — and while a "
        "full game waits for one payment, *Leave the game*."
    ),
)
async def withdraw_yes(
    proposal_id: UUID, acting: ActingDep, withdraw: WithdrawYesDep
) -> Response:
    await withdraw.execute(
        AnswerProposalCommand(proposal_id=proposal_id, player_id=acting)
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --------------------------------------------------------------------------- #
# Leaving, and a rescue's open seat (#593)
# --------------------------------------------------------------------------- #


@router.post(
    "/bookings/{booking_id}/departure",
    response_model=DepartureResponse,
    status_code=status.HTTP_200_OK,
    responses=_REFUSED,
    summary="Leave the game, as this person",
    description=(
        "`POST /api/v1/bookings/{id}/departure` as the acting account: before "
        "the cut-off the hold let go and nothing taken (#637), after it the seat "
        "offered until the start and refunded when it is taken, while a payment "
        "is awaited the yes withdrawn — and the seat offered to the group."
    ),
)
async def leave_the_game(
    booking_id: UUID, acting: ActingDep, leave: LeaveTheGameDep
) -> DepartureResponse:
    left = await leave.execute(
        LeaveTheGameCommand(booking_id=booking_id, player_id=acting)
    )
    return DepartureResponse(left=left)


@router.post(
    "/bookings/{booking_id}/seats",
    response_model=YesAnswerResponse,
    status_code=status.HTTP_200_OK,
    responses={
        **_REFUSED,
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ErrorResponse,
            "description": "As the player's own route answers it.",
        },
    },
    summary="Take the seat, as this person",
    description=(
        "`POST /api/v1/bookings/{id}/seats` as the acting account — *I'm in* on "
        "a rescue: the share held until the cut-off — or taken at once after it "
        "(#637) — over the provider this process moves money through, the seat "
        "that opened first theirs, and a leaver after the cut-off refunded less "
        "exactly the fee kept on their payment (#641). The first join wins."
    ),
)
async def take_the_seat(
    booking_id: UUID, acting: ActingDep, join: JoinARescueDep
) -> YesAnswerResponse:
    answer = await join.execute(RescueCommand(booking_id=booking_id, player_id=acting))
    return YesAnswerResponse.from_answer(answer)


@router.post(
    "/bookings/{booking_id}/no",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    responses=_REFUSED,
    summary="No to a rescue, as this person",
    description=(
        "`POST /api/v1/bookings/{id}/no` as the acting account — *Not this "
        "time* on a Seat open card: it leaves their deck, and the seat stays on "
        "their *Fill in*."
    ),
)
async def say_no_to_the_seat(
    booking_id: UUID, acting: ActingDep, say_no: SayNoToARescueDep
) -> Response:
    await say_no.execute(RescueCommand(booking_id=booking_id, player_id=acting))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --------------------------------------------------------------------------- #
# Posting a game (#593)
# --------------------------------------------------------------------------- #

_POSTING_REFUSED: dict[int | str, dict[str, Any]] = {
    **_REFUSED,
    status.HTTP_400_BAD_REQUEST: {
        "model": ErrorResponse,
        "description": "As the player's own route answers it.",
    },
    status.HTTP_503_SERVICE_UNAVAILABLE: {
        "model": ErrorResponse,
        "description": "As the player's own route answers it.",
    },
}


def _posting(
    player_id: UUID,
    pool_id: UUID,
    *,
    sport: Sport,
    kind: SearchMode,
    who: Who,
    level_low: float | None,
    level_high: float | None,
) -> PostingCommand:
    return PostingCommand(
        player_id=player_id,
        pool_id=pool_id,
        sport=sport,
        kind=kind,
        who=who,
        level_low=level_low,
        level_high=level_high,
    )


@router.get(
    "/pools/{pool_id}/posting-grid/slot",
    response_model=PostingSlotResponse,
    responses=_POSTING_REFUSED,
    summary="A posting grid cell's sheet, as this person",
    description=(
        "`GET /api/v1/pools/{id}/posting-grid/slot` as the acting account: the "
        "free courts the post could be made at — each a court hour *Post a "
        "game* takes — their best fits free then, and what is already "
        "happening there. Nothing is recorded."
    ),
)
async def read_posting_slot(
    pool_id: UUID,
    sport: Sport,
    kind: SearchMode,
    who: Who,
    day: date,
    range_: Annotated[
        DayRange, Query(alias="range", description="A third of the day.")
    ],
    acting: ActingDep,
    read: ReadPostingSlotDep,
    level_low: float | None = None,
    level_high: float | None = None,
) -> PostingSlotResponse:
    slot = await read.execute(
        ReadPostingSlotCommand(
            posting=_posting(
                acting,
                pool_id,
                sport=sport,
                kind=kind,
                who=who,
                level_low=level_low,
                level_high=level_high,
            ),
            day=day,
            day_range=range_,
        )
    )
    return PostingSlotResponse.from_slot(slot)


@router.post(
    "/pools/{pool_id}/posts",
    response_model=PostedResponse,
    status_code=status.HTTP_201_CREATED,
    responses=_POSTING_REFUSED,
    summary="Post a game, as this person",
    description=(
        "`POST /api/v1/pools/{id}/posts` as the acting account — *Post — "
        "you're In*, with the sport, kind, *Who* and Level range, at a court "
        "hour a cell's sheet lists: their yes, and the game dealt to their "
        "best fits free then."
    ),
)
async def post_a_game(
    pool_id: UUID, body: PostRequest, acting: ActingDep, post: PostAGameDep
) -> PostedResponse:
    posted = await post.execute(
        PostAGameCommand(
            posting=_posting(
                acting,
                pool_id,
                sport=body.sport,
                kind=body.kind,
                who=body.who,
                level_low=body.level_low,
                level_high=body.level_high,
            ),
            club_id=body.club_id,
            start=instant(body.starts_at),
        )
    )
    return PostedResponse.from_posted(posted)


# --------------------------------------------------------------------------- #
# After the game: the score (#593); at the court: who turned up (#657)
# --------------------------------------------------------------------------- #

_GAME_REFUSED: dict[int | str, dict[str, Any]] = {
    status.HTTP_400_BAD_REQUEST: {
        "model": ErrorResponse,
        "description": "As the player's own route answers it.",
    },
    status.HTTP_403_FORBIDDEN: {
        "model": ErrorResponse,
        "description": (
            "`not_a_seed_account` — the acting account is not one the seed "
            "created, and nothing was asked of the use case. Any other code as "
            "the player's own route answers it."
        ),
    },
    status.HTTP_409_CONFLICT: {
        "model": ErrorResponse,
        "description": "As the player's own route answers it.",
    },
}


@router.post(
    "/games/{game_id}/result",
    response_model=GameSchema,
    status_code=status.HTTP_200_OK,
    responses=_GAME_REFUSED,
    summary="State a score, as this person",
    description=(
        "`POST /api/v1/games/{id}/result` as the acting account: *we played, "
        "here is the score* — or their side's correction, or their side's one "
        "disagreement with the other's. The record decides which."
    ),
)
async def state_result(
    game_id: UUID,
    payload: StateResultRequest,
    acting: ActingDep,
    state: StateResultDep,
) -> GameSchema:
    return GameSchema.of(
        await state.execute(
            StateResultCommand(
                game_id=game_id, player_id=acting, score=payload.score.as_score()
            )
        ),
        reader_id=acting,
    )


@router.post(
    "/games/{game_id}/result/acceptance",
    response_model=GameSchema,
    status_code=status.HTTP_200_OK,
    responses=_GAME_REFUSED,
    summary="Agree with the score, as this person",
    description=(
        "`POST /api/v1/games/{id}/result/acceptance` as the acting account: the "
        "other side's score agreed with — final at once, and the game closed."
    ),
)
async def accept_result(
    game_id: UUID, acting: ActingDep, accept: AcceptResultDep
) -> GameSchema:
    return GameSchema.of(
        await accept.execute(AcceptResultCommand(game_id=game_id, player_id=acting)),
        reader_id=acting,
    )


class Where(StrEnum):
    """Where the acting account's phone says it is when it taps."""

    #: On the club's own map point.
    AT_THE_CLUB = "AT_THE_CLUB"
    #: Two kilometres north of it.
    AWAY = "AWAY"


#: How far north of the club *away* is.
_AWAY_DEGREES_NORTH = 0.018
#: The accuracy the console's fix claims, in metres.
_CONSOLE_ACCURACY_M = 10.0


class AtTheCourtPress(BaseModel):
    """Who the tap is about, and where the acting account taps it from."""

    player_id: UUID = Field(
        description=(
            "Who it is about: somebody else for *isn't here yet* and *they're "
            "here*, the acting account itself for *I'm here*."
        )
    )
    where: Where = Field(
        description=(
            "`AT_THE_CLUB` sends a fix on the club's map point, `AWAY` one two "
            "kilometres north of it — the player route's own body then."
        )
    )


async def _fix(
    game_id: UUID, where: Where, games: GameRepositoryDep, clubs: GameClubsDep
) -> LocationFix:
    """The fix a phone at the club — or away from it — would send. Read off the
    game's club through the same demand the use case measures against, so the
    press is answered as the phone's tap is; a game or club that cannot be read
    taps from nowhere, and the use case refuses it as the route would."""

    game = await games.load(game_id)
    club = None if game is None else await clubs.of(game.challenge_id)
    latitude, longitude = (
        (0.0, 0.0) if club is None else (club.latitude, club.longitude)
    )
    if where is Where.AWAY:
        latitude = min(90.0, latitude + _AWAY_DEGREES_NORTH)
    return LocationFix(
        latitude=latitude, longitude=longitude, accuracy_m=_CONSOLE_ACCURACY_M
    )


@router.post(
    "/games/{game_id}/attendance/not-here-yet",
    response_model=GameSchema,
    status_code=status.HTTP_200_OK,
    responses=_GAME_REFUSED,
    summary="Say somebody isn't here yet, as this person",
    description=(
        "`POST /api/v1/games/{id}/attendance/not-here-yet` as the acting "
        "account, from the club or away — *Oscar isn't here yet*, in the first "
        "30 minutes of a booked game."
    ),
)
async def note_absent(
    game_id: UUID,
    payload: AtTheCourtPress,
    acting: ActingDep,
    games: GameRepositoryDep,
    clubs: GameClubsDep,
    note: NoteAbsentDep,
) -> GameSchema:
    fix = await _fix(game_id, payload.where, games, clubs)
    return GameSchema.of(
        await note.execute(
            NoteAbsentCommand(
                game_id=game_id,
                player_id=acting,
                absent_id=payload.player_id,
                fix=fix,
            )
        ),
        reader_id=acting,
    )


@router.post(
    "/games/{game_id}/attendance/arrival",
    response_model=GameSchema,
    status_code=status.HTTP_200_OK,
    responses=_GAME_REFUSED,
    summary="Say you're here, or they're here, as this person",
    description=(
        "`POST /api/v1/games/{id}/attendance/arrival` as the acting account, "
        "from the club or away — *I'm here* naming themselves, *they're here* "
        "naming a courtmate."
    ),
)
async def note_arrival(
    game_id: UUID,
    payload: AtTheCourtPress,
    acting: ActingDep,
    games: GameRepositoryDep,
    clubs: GameClubsDep,
    note: NoteArrivalDep,
) -> GameSchema:
    fix = await _fix(game_id, payload.where, games, clubs)
    return GameSchema.of(
        await note.execute(
            NoteArrivalCommand(
                game_id=game_id,
                player_id=acting,
                arrived_id=payload.player_id,
                fix=fix,
            )
        ),
        reader_id=acting,
    )


@router.post(
    "/games/{game_id}/attendance/claim",
    response_model=GameSchema,
    status_code=status.HTTP_200_OK,
    responses=_GAME_REFUSED,
    summary="Say you were there, as this person",
    description=(
        "`POST /api/v1/games/{id}/attendance/claim` as the acting account — *I "
        "was there*, within a day of the tap window closing. No location: the "
        "player route asks none."
    ),
)
async def claim_presence(
    game_id: UUID, acting: ActingDep, claim: ClaimPresenceDep
) -> GameSchema:
    return GameSchema.of(
        await claim.execute(ClaimPresenceCommand(game_id=game_id, player_id=acting)),
        reader_id=acting,
    )


@router.post(
    "/games/{game_id}/attendance/confirmation",
    response_model=GameSchema,
    status_code=status.HTTP_200_OK,
    responses=_GAME_REFUSED,
    summary="Say they were here, as this person",
    description=(
        "`POST /api/v1/games/{id}/attendance/confirmation` as the acting account "
        "— *yes, they were here*: the claimant Came late, and the game carries "
        "on. No location: the player route asks none."
    ),
)
async def confirm_presence(
    game_id: UUID,
    payload: PresenceConfirmationRequest,
    acting: ActingDep,
    confirm: ConfirmPresenceDep,
) -> GameSchema:
    return GameSchema.of(
        await confirm.execute(
            ConfirmPresenceCommand(
                game_id=game_id, player_id=acting, claimant_id=payload.player_id
            )
        ),
        reader_id=acting,
    )
