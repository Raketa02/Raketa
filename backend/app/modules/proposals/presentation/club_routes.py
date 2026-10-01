"""**On request: the club confirms**, on the club surface (#543; the mechanics
§16.8, §16.12, §16.14; the screens B2, B4).

Mounted under ``/api/v1/club``, which only the club website consumes
(``docs/adr/0187`` §5), and it takes a **club-audience** token: a desk answers
its own club's requests. **Signed by this context** because the answer is the
fill's — everybody charged together on the club's yes, the people dealt a new
card on its no — and the fill is ``proposals``'.

**What the club sees of a player is their Name** (§16.14), and on a request
nobody has paid yet.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Response, status
from pydantic import BaseModel, Field

from app.core.exception_handlers import ErrorResponse
from app.engines.matchfit.core import SearchMode
from app.kernel import Sport
from app.modules.clubs.presentation.dependencies import CurrentClubAccountDep
from app.modules.proposals.application.club_requests import (
    REFUSAL_REASON_MAX,
    Acceptance,
    AcceptOutcome,
    WaitingRequests,
)
from app.modules.proposals.domain.deck import GAME_LENGTH
from app.modules.proposals.presentation.dependencies import (
    AcceptTheRequestDep,
    ReadWaitingRequestsDep,
    RefuseTheRequestDep,
)

router = APIRouter(prefix="/bookings", tags=["club"])


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
            "`BOOKED` — everybody paid, the game is booked on `court_name` and "
            "the players are told. `SEAT_OPENED` — a player's payment did not go "
            "through, or a player could no longer be on the game: **nobody "
            "paid**, the request is off and the game is looking for a player "
            "again; you are asked again when it is full."
        )
    )
    court_name: str | None = Field(
        description="The court the players were given — on a booked game only."
    )

    @classmethod
    def from_acceptance(cls, acceptance: Acceptance) -> "AcceptanceResponse":
        return cls(outcome=acceptance.outcome, court_name=acceptance.court_name)


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
        "**Accept** books the game: everybody is charged at this moment, all "
        "together or not at all, on your account — you are the seller — and "
        "the players are given the court that was reserved for them. Their game, "
        "its chat and their receipts open; *It's a game! · you paid* is emailed "
        "to each."
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
