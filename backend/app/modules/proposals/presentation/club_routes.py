"""**The club's Raketa bookings**, on the club surface: **On request — the club
confirms** (#543; the mechanics §16.8, §16.12, §16.14; the screens B2, B4), and
**the club runs them** — a day of bookings, Move, Cancel, and the desk's Check in
(#547; the mechanics §15.1, §16.7, §16.9, §16.10; the screens B4, B6).

Mounted under ``/api/v1/club``, which only the club website consumes
(``docs/adr/0187`` §5), and it takes a **club-audience** token: a desk answers
its own club's requests. **Signed by this context** because the answer is the
fill's — everybody charged together on the club's yes, the people dealt a new
card on its no — and the fill is ``proposals``'.

**What the club sees of a player is their Name, whether they paid, and whether
the desk checked them in** (§16.14) — and on a request nobody has paid yet.
Signed here for the bookings' acts too: a cancel refunds and owes a new card, and
every act on a game locks its proposal first.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Query, Response, status
from pydantic import BaseModel, Field

from app.core.exception_handlers import ErrorResponse
from app.engines.matchfit.core import SearchMode
from app.kernel import Instant, Sport, invariant
from app.modules.clubs.presentation.dependencies import CurrentClubAccountDep
from app.modules.proposals.application.club_bookings import (
    CheckedIn,
    ClubBookingRow,
    ClubDay,
)
from app.modules.proposals.application.club_money import ClubMoney, MoneyRow
from app.modules.proposals.application.club_requests import (
    REFUSAL_REASON_MAX,
    Acceptance,
    AcceptOutcome,
    WaitingRequests,
)
from app.modules.proposals.domain.club_bookings import (
    ClubFilter,
    ClubStatus,
    CourtToMoveTo,
    called_off_for_the_club,
    price_of,
)
from app.modules.proposals.domain.deck import GAME_LENGTH
from app.modules.proposals.domain.home import BookedGame, ClubCancelReason
from app.modules.proposals.presentation.dependencies import (
    AcceptTheRequestDep,
    CancelTheGameDep,
    CheckInAtTheDeskDep,
    MoveTheGameDep,
    ReadClubBookingsDep,
    ReadClubMoneyDep,
    ReadFreeCourtsDep,
    ReadWaitingRequestsDep,
    RefuseTheRequestDep,
)

router = APIRouter(prefix="/bookings", tags=["club"])
#: The desk's Check in page posts here (#547).
check_ins_router = APIRouter(prefix="/check-ins", tags=["club"])
#: The Money page reads here (#548).
money_router = APIRouter(prefix="/money", tags=["club"])


# The five reasons a booking of the club's can come to, as its desk reads them.
# The players' reasons for a game gone back to filling (``BOOK_BY_PASSED``,
# ``COURT_HOUR_LOST``, #624) are never the club's — such a game is on no page
# of its — so the club's document keeps the players' enum's name and its own
# values, and says nothing of them.
class CalledOffReason(StrEnum):
    """Why a game will not be played (the mechanics §14.1, §16.7)."""

    REFUSED = "REFUSED"
    NO_ANSWER = "NO_ANSWER"
    SHORT_AT_THE_CUT_OFF = "SHORT_AT_THE_CUT_OFF"
    CANCELLED_BY_THE_CLUB = "CANCELLED_BY_THE_CLUB"
    #: You said yes, and a player's payment did not come in time (#626).
    PAYMENT_NOT_IN_TIME = "PAYMENT_NOT_IN_TIME"


def _reason_for_the_club(game: BookedGame, *, read_at: Instant) -> CalledOffReason:
    reason = invariant(
        called_off_for_the_club(game, now=read_at),
        f"{game.booking_id} is called off for the club with no reason",
    )
    return CalledOffReason(reason.value)


class WaitingPlayerSchema(BaseModel):
    player_id: UUID
    name: str | None = Field(
        description=(
            "Their Name, whole. `null` for an account that can no longer be named."
        )
    )


class WaitingBookingSchema(BaseModel):
    """A full game asking for a court — **Waiting for you**."""

    booking_id: UUID
    sport: Sport
    kind: SearchMode = Field(description="Competitive, or for fun (a friendly).")
    starts_at: datetime = Field(description="The court hour's start; games are 1 h.")
    ends_at: datetime
    court_name: str = Field(
        description=(
            "The court reserved for the game while you decide — given to the "
            "players with your yes."
        )
    )
    players: list[WaitingPlayerSchema] = Field(
        description="Everybody on the game. Nobody has paid yet."
    )
    price_grosze: int = Field(description="The court's price for the hour.")
    share_grosze: int = Field(description="Each player's share of it.")
    answer_by: datetime = Field(
        description=(
            "When your time to confirm runs out — the countdown. Past it the "
            "request is called off as unanswered: nobody pays and the hour is "
            "yours to sell again."
        )
    )


class WaitingBookingsResponse(BaseModel):
    """Everything waiting for the club's answer — the Overview's *waiting for
    your answer*, the Bookings page's *Waiting for you*, and its badge."""

    read_at: datetime = Field(
        description="The instant the list was read at — what each countdown runs from."
    )
    bookings: list[WaitingBookingSchema] = Field(
        description="The one due first, first. Empty: *Nothing is waiting for you.*"
    )

    @classmethod
    def from_waiting(cls, waiting: WaitingRequests) -> "WaitingBookingsResponse":
        return cls(
            read_at=waiting.read_at,
            bookings=[
                WaitingBookingSchema(
                    booking_id=request.booking_id,
                    sport=request.sport,
                    kind=request.kind,
                    starts_at=request.start,
                    ends_at=request.start + GAME_LENGTH,
                    court_name=request.court_name,
                    players=[
                        WaitingPlayerSchema(
                            player_id=player, name=waiting.names.get(player)
                        )
                        for player in request.players
                    ],
                    price_grosze=request.price_grosze,
                    share_grosze=request.share_grosze,
                    answer_by=request.answer_by,
                )
                for request in waiting.requests
            ],
        )


class AcceptanceResponse(BaseModel):
    outcome: AcceptOutcome = Field(
        description=(
            "`BOOKED` — every share is held, and taken at your cut-off (or "
            "taken now, after it — #637); the game is booked on `court_name` and "
            "the players are told. `WAITING_FOR_A_PAYMENT` — accepted, and one "
            "player's payment did not go through (#626): **your yes and the "
            "court are kept** until `payment_due_by` while they pay. Nobody has "
            "paid yet; when they do, it is booked and you are not asked again, "
            "and if they don't, it is called off and you are emailed *A game "
            "didn't go ahead*. `CALLED_OFF` — a player's payment did not go "
            "through and the game's last moment to book had come, so there was "
            "no time to pay: called off, nobody paid, and the hour is yours to "
            "sell again. `SEAT_OPENED` — a player could no longer be on the "
            "game: **nobody paid**, the request is off and the game is looking "
            "for a player again; you are asked again when it is full."
        )
    )
    court_name: str | None = Field(
        description="The court the players were given — on a booked game only."
    )
    payment_due_by: datetime | None = Field(
        default=None,
        description=(
            "When the player's payment is due — *Accepted · waiting for one "
            "player's payment until 21:20*. Never who. `WAITING_FOR_A_PAYMENT` "
            "only."
        ),
    )

    @classmethod
    def from_acceptance(cls, acceptance: Acceptance) -> "AcceptanceResponse":
        return cls(
            outcome=acceptance.outcome,
            court_name=acceptance.court_name,
            payment_due_by=acceptance.pay_by,
        )


class RefusalRequest(BaseModel):
    reason: str | None = Field(
        default=None,
        max_length=REFUSAL_REASON_MAX,
        description=(
            "Why, for your own records — **never shown to the players**, who "
            "read *Called off · refused*. Blank is no reason."
        ),
    )


_NOT_FOUND: dict[int | str, dict[str, Any]] = {
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponse,
        "description": "`booking_not_found` — no such booking at this club.",
    }
}

_NOT_WAITING = (
    "`request_not_waiting` — the game is not waiting for your answer: you "
    "already answered, a player left and it is looking for a player again, or "
    "it was called off as unanswered. `request_timed_out` — your time to "
    "confirm ran out: it is called off as unanswered. Nothing was recorded."
)


@router.get(
    "/waiting",
    response_model=WaitingBookingsResponse,
    status_code=status.HTTP_200_OK,
    summary="What is waiting for your answer",
    description=(
        "Every Raketa game at this club waiting for its answer — an **On "
        "request** club's full games, each asking for a court — with the "
        "players, the hour, the sport, the price and the countdown. Nobody has "
        "paid. A request whose time to confirm has run out is not listed."
    ),
)
async def waiting(
    account: CurrentClubAccountDep, read: ReadWaitingRequestsDep
) -> WaitingBookingsResponse:
    return WaitingBookingsResponse.from_waiting(await read.execute(account.club_id))


@router.post(
    "/{booking_id}/acceptance",
    response_model=AcceptanceResponse,
    status_code=status.HTTP_200_OK,
    responses={
        **_NOT_FOUND,
        status.HTTP_409_CONFLICT: {"model": ErrorResponse, "description": _NOT_WAITING},
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ErrorResponse,
            "description": (
                "`payments_unavailable` — the payment provider could not be "
                "reached to charge the players. Nothing was recorded; retry."
            ),
        },
    },
    summary="Accept a request",
    description=(
        "**Accept** books the game: every share is held at this moment, all "
        "together or not at all, on your account — you are the seller — and "
        "taken at your cut-off, or at once when you accept after it (#637); the "
        "players are given the court that was reserved for them. Their game and "
        "its chat open; *It's a game! · 30 zł held* (*you paid* after the "
        "cut-off) is emailed to each."
    ),
)
async def accept(
    booking_id: UUID, account: CurrentClubAccountDep, accept: AcceptTheRequestDep
) -> AcceptanceResponse:
    return AcceptanceResponse.from_acceptance(
        await accept.execute(club_id=account.club_id, booking_id=booking_id)
    )


@router.post(
    "/{booking_id}/refusal",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    responses={
        **_NOT_FOUND,
        status.HTTP_409_CONFLICT: {"model": ErrorResponse, "description": _NOT_WAITING},
    },
    summary="Refuse a request",
    description=(
        "**Refuse**, with a note for your own records if you like: nobody paid, "
        "the hour is yours to sell again, and the players read *Called off · "
        "refused* and are dealt a new card first — never this court hour again."
    ),
)
async def refuse(
    booking_id: UUID,
    account: CurrentClubAccountDep,
    refuse: RefuseTheRequestDep,
    payload: RefusalRequest | None = None,
) -> Response:
    await refuse.execute(
        club_id=account.club_id,
        booking_id=booking_id,
        reason=None if payload is None else payload.reason,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --------------------------------------------------------------------------- #
# The club runs its bookings (#547)
# --------------------------------------------------------------------------- #


class ClubBookingPlayerSchema(BaseModel):
    """A player on the game, as the club sees them — **a name, whether they
    paid or their share is only held, and whether the desk checked them in**,
    and nothing else (§16.14)."""

    player_id: UUID
    name: str | None = Field(
        description=(
            "Their Name, whole. `null` for an account that can no longer be named."
        )
    )
    paid: bool = Field(description="Their share was taken — *paid ✓*.")
    held: bool = Field(
        description=(
            "Their share is held on their card, and taken at the cut-off — "
            "*held*. Not paid, and not in `collected_grosze` (#637). Never "
            "`true` with `paid`."
        )
    )
    checked_in_at: datetime | None = Field(
        description="When the desk checked them in — *checked in ✓* — or `null`."
    )


class ClubBookingMoneySchema(BaseModel):
    price_grosze: int = Field(description="The court's price for the hour.")
    collected_grosze: int = Field(
        description=(
            "Every share taken from the players, on your account — at your "
            "cut-off, or at once after it. A share only held is not collected "
            "(#637)."
        )
    )
    refunded_grosze: int = Field(
        description=(
            "Everything given back of a share taken — to a leaver whose seat "
            "was taken after the cut-off, less the card fee; in full on a game "
            "cancelled after it. A hold let go before the cut-off refunds "
            "nothing: nothing was taken. Refunds are automatic: you never "
            "refund anybody by hand."
        )
    )


class BookedFromSchema(BaseModel):
    """The group the game was booked in — *where it came from*."""

    group_id: UUID
    name: str
    official: bool = Field(
        description="One of your official groups — or `false`, a player group."
    )


class ClubCountsSchema(BaseModel):
    """How many of the day's bookings each filter shows."""

    all: int
    waiting_for_you: int
    seat_open: int
    called_off: int


class ClubBookingSchema(BaseModel):
    """One Raketa booking at the club."""

    booking_id: UUID
    starts_at: datetime = Field(description="The court hour's start; games are 1 h.")
    ends_at: datetime
    court_name: str = Field(
        description=(
            "The court it is on — reserved for it, while it waits for your answer."
        )
    )
    sport: Sport
    kind: SearchMode = Field(description="Competitive, or for fun (a friendly).")
    status: ClubStatus = Field(
        description=(
            "`WAITING_FOR_YOU` — an On request game asking for the court: Accept "
            "or Refuse before `answer_by`. `WAITING_FOR_A_PAYMENT` — you "
            "accepted, and one player's payment is still to come until "
            "`payment_due_by` (#626): *Accepted · waiting for one player's "
            "payment until 21:20*. Your yes and the court are kept; nothing for "
            "you to answer. `BOOKED` — full; each share held until your cut-off "
            "and taken at it (#637). `SEAT_OPEN` — "
            "a player left and Raketa is finding a replacement; before the "
            "cut-off, a seat still open at it calls the game off and the court "
            "comes back to you. `CALLED_OFF` — see `called_off_reason`; everybody "
            "was refunded or nobody paid, and the hour is free again. `PLAYED` — "
            "the hour has passed; you are paid whatever happened on the court."
        )
    )
    called_off_reason: CalledOffReason | None = Field(
        description=(
            "Why a `CALLED_OFF` game will not be played — `null` otherwise. "
            "`SHORT_AT_THE_CUT_OFF` — a seat was still empty at your cut-off. "
            "`CANCELLED_BY_THE_CLUB` — you cancelled it (`cancel_reason`). "
            "`REFUSED` — you refused the request. `NO_ANSWER` — it was not "
            "answered in time. `PAYMENT_NOT_IN_TIME` — you accepted, and a "
            "player's payment didn't come in time: nobody paid, and you were "
            "emailed *A game didn't go ahead*. Full again, the game asks you "
            "again as a new request."
        )
    )
    cancel_reason: ClubCancelReason | None = Field(
        description="Why you cancelled it — on a game you cancelled, else `null`."
    )
    players: list[ClubBookingPlayerSchema] = Field(
        description="Everybody with a seat on it, the first side first."
    )
    open_seats: int = Field(description="Seats a leaver left open.")
    money: ClubBookingMoneySchema
    booked_from: BookedFromSchema | None = Field(
        description="The group it came from — `null` for a group that is gone."
    )
    answer_by: datetime | None = Field(
        description="Your countdown, while it waits for your answer — else `null`."
    )
    payment_due_by: datetime | None = Field(
        description=(
            "When the player's payment your yes waits on is due — "
            "`WAITING_FOR_A_PAYMENT` only, else `null`. Never who."
        )
    )
    may_move_or_cancel: bool = Field(
        description=(
            "**Move** and **Cancel** are yours: booked or with a seat open, and "
            "not started yet."
        )
    )

    @classmethod
    def of(cls, row: ClubBookingRow, *, day: ClubDay) -> "ClubBookingSchema":
        game = row.game
        return cls(
            booking_id=game.booking_id,
            starts_at=game.start,
            ends_at=game.start + GAME_LENGTH,
            court_name=game.court_name,
            sport=game.sport,
            kind=game.kind,
            status=row.status,
            called_off_reason=_reason_for_the_club(game, read_at=day.read_at)
            if row.status is ClubStatus.CALLED_OFF
            else None,
            cancel_reason=(
                game.cancel_reason if row.status is ClubStatus.CALLED_OFF else None
            ),
            players=[
                ClubBookingPlayerSchema(
                    player_id=player,
                    name=day.names.get(player),
                    paid=player in row.takings.paid,
                    held=player in row.takings.held,
                    checked_in_at=game.checked_in.get(player),
                )
                for player in game.players
            ],
            open_seats=game.open_seats,
            money=ClubBookingMoneySchema(
                price_grosze=price_of(game),
                collected_grosze=row.takings.collected_grosze,
                refunded_grosze=row.takings.refunded_grosze,
            ),
            booked_from=(
                None
                if row.booked_from is None
                else BookedFromSchema(
                    group_id=game.pool_id,
                    name=row.booked_from.name,
                    official=row.booked_from.official,
                )
            ),
            answer_by=(
                game.answer_by if row.status is ClubStatus.WAITING_FOR_YOU else None
            ),
            payment_due_by=(
                game.pay_by if row.status is ClubStatus.WAITING_FOR_A_PAYMENT else None
            ),
            may_move_or_cancel=row.still_to_be_played,
        )


class ClubBookingsResponse(BaseModel):
    """One day of the club's Raketa bookings — the Bookings page."""

    day: date = Field(description="The club's calendar day read.")
    read_at: datetime = Field(
        description="The instant every status and countdown here was read at."
    )
    filter: ClubFilter
    counts: ClubCountsSchema
    bookings: list[ClubBookingSchema] = Field(
        description=("Soonest first. Empty: *No Raketa bookings on this day.*")
    )

    @classmethod
    def of(cls, day: ClubDay) -> "ClubBookingsResponse":
        return cls(
            day=day.day,
            read_at=day.read_at,
            filter=day.chosen,
            counts=ClubCountsSchema(
                all=day.counts[ClubFilter.ALL],
                waiting_for_you=day.counts[ClubFilter.WAITING_FOR_YOU],
                seat_open=day.counts[ClubFilter.SEAT_OPEN],
                called_off=day.counts[ClubFilter.CALLED_OFF],
            ),
            bookings=[ClubBookingSchema.of(row, day=day) for row in day.rows],
        )


class CourtToMoveToSchema(BaseModel):
    court_id: UUID
    name: str

    @classmethod
    def of(cls, court: CourtToMoveTo) -> "CourtToMoveToSchema":
        return cls(court_id=court.court_id, name=court.name)


class FreeCourtsResponse(BaseModel):
    courts: list[CourtToMoveToSchema] = Field(
        description=(
            "Every other court of the game's sport you still have for Raketa at "
            "its hour, in your own order. Empty: there is none — **Cancel** with "
            "*repair* if the court cannot be played."
        )
    )


class MoveRequest(BaseModel):
    court_id: UUID = Field(description="One of the game's free courts.")


class CancelRequest(BaseModel):
    reason: ClubCancelReason = Field(
        description=(
            "`WEATHER`, `REPAIR`, `DOUBLE_BOOKING` or `OTHER` — told to the "
            "players with what comes of their money."
        )
    )


class CheckInRequest(BaseModel):
    code: str = Field(
        min_length=1,
        max_length=200,
        description=(
            "What the camera read off the player's QR code, or the six-character "
            "short code typed by hand — spaces, dashes and case do not matter."
        ),
    )


class CheckedInPlayerSchema(BaseModel):
    player_id: UUID
    name: str | None


class CheckInResponse(BaseModel):
    """The booking and the player — *19:00 · Court 2 · Padel*, *Piotr S. —
    checked in ✓*."""

    booking_id: UUID
    starts_at: datetime
    ends_at: datetime
    court_name: str
    sport: Sport
    kind: SearchMode
    player: CheckedInPlayerSchema
    checked_in_at: datetime

    @classmethod
    def of(cls, checked: CheckedIn) -> "CheckInResponse":
        game = checked.game
        return cls(
            booking_id=game.booking_id,
            starts_at=game.start,
            ends_at=game.start + GAME_LENGTH,
            court_name=game.court_name,
            sport=game.sport,
            kind=game.kind,
            player=CheckedInPlayerSchema(
                player_id=checked.player_id, name=checked.name
            ),
            checked_in_at=checked.at,
        )


_NOT_TO_BE_PLAYED = (
    "`booking_not_booked` — it is waiting for your answer: accept or refuse it. "
    "`booking_is_called_off` — it is off already. `game_has_started` — its hour "
    "has begun. Nothing was recorded."
)


@router.get(
    "",
    response_model=ClubBookingsResponse,
    status_code=status.HTTP_200_OK,
    summary="Your bookings, by day",
    description=(
        "Every Raketa booking at this club on one of its calendar days — the "
        "Bookings page — each with its status, its players (name, *paid*, "
        "*checked in*), its money (the court's price, collected, refunded) and "
        "the group it came from. `filter` narrows the list; `counts` are the "
        "whole day's. A request a player's leaving took back is not listed: "
        "it comes back when the game is full and asks again."
    ),
)
async def bookings_on_a_day(
    account: CurrentClubAccountDep,
    read: ReadClubBookingsDep,
    day: date | None = Query(
        default=None, alias="date", description="The day — today when left out."
    ),
    chosen: ClubFilter = Query(default=ClubFilter.ALL, alias="filter"),
) -> ClubBookingsResponse:
    return ClubBookingsResponse.of(
        await read.execute(account.club_id, day=day, chosen=chosen)
    )


@router.get(
    "/{booking_id}/free-courts",
    response_model=FreeCourtsResponse,
    status_code=status.HTTP_200_OK,
    responses={
        **_NOT_FOUND,
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": _NOT_TO_BE_PLAYED,
        },
    },
    summary="Where a game can be moved",
    description="The Move dialog: the free courts of the game's sport at its hour.",
)
async def free_courts(
    booking_id: UUID, account: CurrentClubAccountDep, read: ReadFreeCourtsDep
) -> FreeCourtsResponse:
    courts = await read.execute(club_id=account.club_id, booking_id=booking_id)
    return FreeCourtsResponse(courts=[CourtToMoveToSchema.of(one) for one in courts])


@router.post(
    "/{booking_id}/move",
    response_model=CourtToMoveToSchema,
    status_code=status.HTTP_200_OK,
    responses={
        **_NOT_FOUND,
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": (
                f"{_NOT_TO_BE_PLAYED} `court_not_free` — that court is not a free "
                "court of the game's sport at its hour. `court_just_taken` — "
                "another game took it a moment ago; read the free courts again."
            ),
        },
    },
    summary="Move a game to another court",
    description=(
        "**Move** a booked game — whole or with a seat open — onto another free "
        "court of its sport at the same hour, until it starts. The players read "
        "the new number; nothing else about the game changes. Answers the court "
        "it is on now."
    ),
)
async def move(
    booking_id: UUID,
    payload: MoveRequest,
    account: CurrentClubAccountDep,
    move: MoveTheGameDep,
) -> CourtToMoveToSchema:
    return CourtToMoveToSchema.of(
        await move.execute(
            club_id=account.club_id, booking_id=booking_id, court_id=payload.court_id
        )
    )


@router.post(
    "/{booking_id}/cancellation",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    responses={
        **_NOT_FOUND,
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": _NOT_TO_BE_PLAYED,
        },
    },
    summary="Cancel a game",
    description=(
        "**Cancel** a booked game, with your reason, until it starts. **Before "
        "your cut-off** every share is only held, and every hold is let go: "
        "nothing was taken, nobody is refunded and nobody pays a fee, you "
        "included (#637). **After it** everybody is **refunded in full** — the "
        "card fees on those payments are not returned, and as the seller you "
        "bear them. Either way it goes on **nobody's record**, the hour is "
        "yours to sell again, and the players are told you cancelled, with the "
        "reason, and dealt a new game first."
    ),
)
async def cancel(
    booking_id: UUID,
    payload: CancelRequest,
    account: CurrentClubAccountDep,
    cancel: CancelTheGameDep,
) -> Response:
    await cancel.execute(
        club_id=account.club_id, booking_id=booking_id, because=payload.reason
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@check_ins_router.post(
    "",
    response_model=CheckInResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": (
                "`check_in_code_unknown` — the code opens no seat: mistyped, or "
                "a seat its player left."
            ),
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": (
                "`check_in_is_off` — you have not switched on *We check players "
                "in*. `check_in_code_for_another_day` — a seat here on another "
                "day (`details.starts_at`). `check_in_code_for_another_club` — a "
                "seat at another club. `already_checked_in` — scanned already "
                "(`details.checked_in_at`: *Checked in at 18:52*). "
                "`booking_is_called_off` — the game is off."
            ),
        },
    },
    summary="Check a player in",
    description=(
        "**Check in** a player on the game's day: the code the camera read off "
        "their QR, or the short code typed by hand. They were there, and can "
        "never be reported as not coming. **Money never depends on it** — you "
        "are paid whether people come or not."
    ),
)
async def check_in(
    payload: CheckInRequest,
    account: CurrentClubAccountDep,
    check_in: CheckInAtTheDeskDep,
) -> CheckInResponse:
    return CheckInResponse.of(
        await check_in.execute(club_id=account.club_id, code=payload.code)
    )


# --------------------------------------------------------------------------- #
# Money (#548)
# --------------------------------------------------------------------------- #


class MoneyTotalsSchema(BaseModel):
    collected_grosze: int = Field(
        description=(
            "Every share taken from the players — at your cut-off, or at once "
            "after it; never a share only held (#637)."
        )
    )
    refunded_grosze: int = Field(
        description=(
            "Everything given back — automatically: you never refund anybody by hand."
        )
    )
    card_fees_grosze: int = Field(
        description=(
            "The provider's card fee on every share taken, yours to pay as at "
            "your own terminal. A refund never returns it."
        )
    )
    net_grosze: int = Field(
        description=(
            "Yours: collected, less refunded, less the card fees. Below nought "
            "when games given back whole cost you their card fees."
        )
    )


class MoneyBookingSchema(BaseModel):
    """One booking's money, on your account — you are the seller."""

    booking_id: UUID
    starts_at: datetime = Field(description="The court hour's start — the row's date.")
    court_name: str
    sport: Sport
    status: ClubStatus = Field(
        description="What the booking is now, as on the Bookings page."
    )
    collected_grosze: int
    refunded_grosze: int
    card_fees_grosze: int
    net_grosze: int
    paid_out: bool = Field(
        description=(
            "A payout carried its money to your bank. Until then it waits on "
            "your account: **you are paid after the game is played**, at the "
            "close of its day, since a refund before the start comes out of it."
        )
    )

    @classmethod
    def of(cls, row: MoneyRow) -> "MoneyBookingSchema":
        game, takings = row.game, row.takings
        return cls(
            booking_id=game.booking_id,
            starts_at=game.start,
            court_name=game.court_name,
            sport=game.sport,
            status=row.status,
            collected_grosze=takings.collected_grosze,
            refunded_grosze=takings.refunded_grosze,
            card_fees_grosze=takings.card_fees_grosze,
            net_grosze=takings.net_grosze,
            paid_out=takings.paid_out,
        )


class ClubMoneyResponse(BaseModel):
    """A month of your Raketa money — the Money page."""

    month: str = Field(description="The month read, `YYYY-MM`.", examples=["2026-10"])
    read_at: datetime
    totals: MoneyTotalsSchema = Field(description="The month's, at the top.")
    bookings: list[MoneyBookingSchema] = Field(
        description=(
            "Every booking played — or to be played — in the month that took "
            "money, soonest first. A request nobody paid for is not money and "
            "is not listed."
        )
    )

    @classmethod
    def of(cls, money: ClubMoney) -> "ClubMoneyResponse":
        totals = money.totals
        return cls(
            month=f"{money.month:%Y-%m}",
            read_at=money.read_at,
            totals=MoneyTotalsSchema(
                collected_grosze=totals.collected_grosze,
                refunded_grosze=totals.refunded_grosze,
                card_fees_grosze=totals.card_fees_grosze,
                net_grosze=totals.net_grosze,
            ),
            bookings=[MoneyBookingSchema.of(row) for row in money.rows],
        )


#: A month as the page asks for it.
_MONTH = r"^\d{4}-(0[1-9]|1[0-2])$"


@money_router.get(
    "",
    response_model=ClubMoneyResponse,
    status_code=status.HTTP_200_OK,
    summary="Your money, by month",
    description=(
        "A month of your Raketa money, booking by booking — by the day each "
        "game is played on — with what the players paid, what was given back, "
        "the card fees and what is yours, and the month's totals. **You are the "
        "seller**: every figure is your own account's. Your payouts are "
        "`GET /api/v1/club/payouts`."
    ),
)
async def money_by_month(
    account: CurrentClubAccountDep,
    read: ReadClubMoneyDep,
    month: str | None = Query(
        default=None,
        pattern=_MONTH,
        description="`YYYY-MM` — this month when left out.",
    ),
) -> ClubMoneyResponse:
    return ClubMoneyResponse.of(
        await read.execute(
            account.club_id,
            month=None if month is None else date.fromisoformat(f"{month}-01"),
        )
    )
